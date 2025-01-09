import numpy as np
import pandas as pd
import sys
import os
from scipy import stats
import json
import pickle
from sklearn.model_selection import LeaveOneOut,KFold,cross_val_score, train_test_split
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import mean_squared_error
import warnings
warnings.filterwarnings('ignore')

def rsquared(x, y): 
    """Return the metriscs coefficient of determination (R2)
    Parameters:
    -----------
    x (numpy array or list): Predicted variables
    y (numpy array or list): Observed variables
    """
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y) 
    a = r_value**2
    return a
    
def vip(x, y, model):
    """Return the Variable Importance in Projection (VIP) metric for trained PLSR model.
    Parameters:
    -----------
    x (numpy array, shape = (len(x),num_bands)): the training reflectance
    y (numpy array, shape  = len(x),1): the training variables
    model: the trained PLSE model.
    """
    t = model.x_scores_
    w = model.x_weights_
    q = model.y_loadings_
    
    m, p = x.shape
    _, h = t.shape
    vips = np.zeros((p,))

    s = np.diag(t.T @ t @ q.T @ q).reshape(h, -1)
    total_s = np.sum(s)

    for i in range(p):
        weight = np.array([ (w[i,j] / np.linalg.norm(w[:,j]))**2 for j in range(h)])
        vips[i] = np.sqrt(p*(s.T @ weight)/total_s)
    return vips

def press(train_X,train_y,test_X,test_y, tr, iteration):
    press_scores = []
    for i in np.arange(1,train_X.shape[1]+1):
    # for i in np.arange(1,21):
        pls = PLSRegression(n_components=i)
        pls.fit(train_X, train_y[tr])
        
        pred = pls.predict(test_X)
        aa = np.array(pred.reshape(-1,).tolist())
        bb = np.array(test_y[tr].tolist())
        score = np.sum((aa - bb) ** 2)
        press_scores.append(score)
    n_components = press_scores.index(min(press_scores))+1
    print(f"{tr} model: iteration {iteration+1}_random CV_n_components: {n_components}")
    press_scores = pd.DataFrame({'ncomp': np.arange(1,X.shape[1]+1), f'PRESS_score_{iteration+1}': press_scores})
    # press_scores = pd.DataFrame({'ncomp': np.arange(1,21), f'PRESS_score_iteration_{iteration+1}': press_scores})
    return press_scores, n_components

def random_CV(X,y,tr,n_iterations, out_path):
    """Random cross-validation of PLSR model for estimating leaf traits.
    Parameters:
    -----------
    X (numpy array): leaf spectra data used for PLSR modeling
    y (numpy array): leaf trait data used for PLSR modeling
    tr (str): trait name ("Chla+b", "Ccar", "EWT", "LMA" or Nitrogen)
    n_iterations (int): How many iterations to train the PLSR model.

    Output files:
    -----------
    (1) Leaf trait predictions in *.csv format.
    (2) PLSR VIP metric in *.csv format.
    (3) PLSR coefficients in *.csv format.
    (4) PRESS score for determining n_components
    """
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
    
    plsr_coef = pd.DataFrame(np.zeros(shape = (n_iterations, X.shape[1])),columns = X.columns)
    vip_score = pd.DataFrame(np.zeros(shape = (n_iterations, X.shape[1])),columns = X.columns)
    
    var_start = True
    k = 0
    for iteration in range(n_iterations):
        XX_train, XX_test, yy_train, yy_test = train_test_split(X_train, y_train, test_size=0.2, random_state=iteration)
        press_scores, n_components = press(XX_train,yy_train,XX_test,yy_test, tr, iteration)
        
        pls = PLSRegression(n_components=n_components)
        pls.fit(XX_train, yy_train[tr])
        with open(f'{out_path}saved_models/{tr}_PLSR_model_interation{iteration+1}.pkl', 'wb') as f:
            pickle.dump(pls, f)
            
        coef = pls.coef_
        vvv = vip(XX_train, yy_train[tr], pls)
        plsr_coef.iloc[k] = coef
        vip_score.iloc[k] = vvv
        
        pred = pls.predict(X_test)
        pred = pd.DataFrame(pred,columns = [f'iteration_{iteration+1}'])
        
        if var_start:
            all_press = press_scores
            iterative_pred = pred
            var_start = False
        else:
            all_press = all_press.merge(press_scores, on='ncomp')
            iterative_pred = pd.concat([iterative_pred,pred], axis = 1)
        k = k+1
    y_test.reset_index(drop = True, inplace = True)
    df = pd.concat([y_test,iterative_pred], axis = 1)
    df["mean"] = iterative_pred.mean(axis = 1)
    df["std"] = iterative_pred.std(axis = 1)
    
    prefix = f"{out_path}{tr}_random CV_"
    df.to_csv(f"{prefix}df.csv", index=False)
    vip_score.to_csv(f"{prefix}VIP.csv", index=False)
    plsr_coef.to_csv(f"{prefix}coefficients.csv", index=False)
    all_press.to_csv(f"{prefix}press.csv", index=False)
    return

#####################################################
data_path = "/mnt/cephfs/scratch/groups/chen_group/FujiangJi/NEON_PLSR/5_merged_csv_data/"
file_name = f"{data_path}2020 and 2021 NEON extracted leaf traits and spectra data_NBAR_add_LAI.csv"
data = pd.read_csv(file_name)
data.dropna(axis=1, how = "all", inplace = True)
data.dropna(axis=0, inplace = True)

tr_name = ["Chla+b", 'Ccar', 'EWT', "Nitrogen"]
PFTs = data["PFT"].unique().tolist()
PFTs = ["all_data"] + PFTs

for pft in PFTs[0:1]:
    print(pft)
    os.makedirs(f"/mnt/cephfs/scratch/groups/chen_group/FujiangJi/NEON_PLSR/6_PLSR_results/1_add_LAI/{pft}", exist_ok=True)
    out_path = f"/mnt/cephfs/scratch/groups/chen_group/FujiangJi/NEON_PLSR/6_PLSR_results/1_add_LAI/{pft}/"
    os.makedirs(f"{out_path}/saved_models", exist_ok=True)
    if pft == "all_data":
        data_use = data.copy()
    else:
        data_use = data[data["PFT"] == pft]

    for tr in tr_name:
        print(tr)    ### units = {"Chla+b":"µg/cm²", "Ccar":"µg/cm²", "EWT":"g/m²", "Nitrogen":"µg/cm²"}
        data_use = data_use[data_use[tr]>0]
        print(f"total samples of {tr}: {len(data)} samples.")

        X = pd.concat([data_use.loc[:,'406.99':"2313.2"], pd.DataFrame(data_use.loc[:,"LAI"])], axis = 1)
        y = data_use.loc[:,:"crs"]
        if tr == "Chla+b":
            print(f"number of bands of {tr}: {X.shape[1]} bands.")
            print(f"wavelength: {X.columns.tolist()}")
        n_iterations = 100
        random_CV(X,y,tr,n_iterations, out_path)