### Revised from: https://github.com/irea-cnr-mi/prismaread/; 
###               https://irea-cnr-mi.github.io/prismaread/articles/Importing-Level-2-Data.html

#install.packages("remotes")
#if (!require(prismaread)) remotes::install_github("irea-cnr-mi/prismaread")
library(prismaread)

#if (!require(rgdal)) install.packages("https://cran.r-project.org/src/contrib/Archive/rgdal/rgdal_1.6-6.tar.gz", repos = NULL, type = "source")
library(rgdal)

# Set the working directory
setwd("E:/Volumes/data/PRISMA_L2D")
# Assign and check the working directory
folder_name <- getwd()

images_folder <- c("D01_BART", "D01_HARV", "D02_SCBI", "D03_OSBS", "D07_MLBS", "D07_ORNL", 
                   "D08_TALL", "D10_CPER", "D13_MOAB", "D14_JORN", "D16_WREF")

error_files <- c()
for (folder in images_folder) {
  path <- paste0(folder_name, "/", folder)
  l2d_out_dir <- paste0(folder_name, "/", "PRISMA_L2D_tif","/", folder)
  dir.create(l2d_out_dir, recursive = TRUE, showWarnings = FALSE)
  l2d_he5 <- paste0(folder_name, "/", "PRISMA_L2D_he5","/", folder)
  dir.create(l2d_he5, recursive = TRUE, showWarnings = FALSE)
  
  files <- list.files(path = path, full.names = TRUE)
  for (file in files) {
    tryCatch({
      unzip(zipfile = file, exdir = l2d_he5)
      file_name <- basename(file)
      file_name <- sub("\\.zip$", "", file_name)
      l2d_he5_path <- paste0(l2d_he5, "/", file_name, '.he5')
      pr_convert(
        in_file = l2d_he5_path,
        out_folder = l2d_out_dir,
        out_format = "GTiff",
        VNIR = TRUE,
        SWIR = TRUE,
        PAN = TRUE,
        FULL = TRUE,
        join_priority = "SWIR",
        LATLON = TRUE,
        ANGLES = TRUE,
        overwrite = TRUE,
        ERR_MATRIX = TRUE,
        CLOUD = TRUE)
    }, warning = function(w) {
      message(paste("Warning unzipping file:", file))
      error_files <<- c(error_files, file)
      file_name <- basename(file)
      file_name <- sub("\\.zip$", "", file_name)
      l2d_he5_path <- paste0(l2d_he5, "/", file_name, '.he5')
      unlink(l2d_he5_path)
      return(NULL)
    }, error = function(e) {
      message(paste("Error unzipping file:", file))
      error_files <<- c(error_files, file)
      file_name <- basename(file)
      file_name <- sub("\\.zip$", "", file_name)
      l2d_he5_path <- paste0(l2d_he5, "/", file_name, '.he5')
      unlink(l2d_he5_path)
      return(NULL)
    })
  }
  #unlink(l2d_he5, recursive = TRUE)
}
#unlink(paste0(folder_name, "/", "PRISMA_L2D_he5"), recursive = TRUE)
writeLines(error_files, "error_files.txt")




