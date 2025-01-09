# 3.2 Smooth the spectra data.
 # step 1: remove the spikes occurring along-track at specific wavelengths using the findpeaks function with a threshold of 0.018;
 # step 2: the spectral regions around the atmospheric gaseous absorptions presenting anomalous spikes and dips likely related to the spectral shift of the instrument were systematically excluded  (i.e., 535–550, 755–780, 755–775, 810–855, 885–970, 1015–1050, 1080–1165, 1225–1285, 1330–1490, 1685–1700, 1725–1750, 1780–1960, 1990–2030 nm).
 # step 3: the remaining spectral bands were spline-smooth interpolated using the SplineSmoothGapfilling function included in the FieldSpectroscopyCC package with 60 degrees of freedom.
 #step 4: the atmospheric water absorption regions (i.e., 1350–1510 and 1795–2000 nm) and the last portion of the SWIR (i.e., 2320–2500 nm) were excluded.

#install.packages("remotes")
#remotes::install_github("tommasojulitta/FieldSpectroscopyCC")
library(FieldSpectroscopyCC)
#install.packages("pracma")
library(pracma)
#install.packages("foreach")
library(foreach)
#install.packages("doParallel")
library(doParallel)
#install.packages("progress")
library(progress)

# Set the number of cores to be used
num_cores <- parallel::detectCores()
registerDoParallel(num_cores)

is_within_range <- function(value, ranges) {
  any(sapply(ranges, function(x) value >= x[1] & value <= x[2]))
}

process_chunk <- function(chunk, wl, ranges, range2) {
  smooth_chunk <- NULL
  for (i in 1:nrow(chunk)) {
    spectra <- as.numeric(chunk[i, ])
    peaks <- findpeaks(spectra, threshold = 0.018)
    peaks <- peaks[,2:4]
    spectra[peaks] <- NA
    idx <- which(sapply(wl, is_within_range, ranges))
    spectra[idx] <- NA
    
    data <- data.frame(wl = wl, reflectance = spectra)
    smoothed_spectra <- SplineSmoothGapfilling(wl=data$wl,spectrum = data$reflectance, df = 60)
    idx2 <- which(sapply(wl, is_within_range, range2))
    smoothed_spectra[idx2] <- NA
    
    smooth_chunk <- rbind(smooth_chunk, smoothed_spectra)
  }
  return(smooth_chunk)
}

data_path <- "/Volumes/data/PRISMA_imagery_array/"
folders <- list.dirs(data_path, full.names = FALSE, recursive = FALSE)
out_path <-"/Volumes/data/PRISMA_imagery_smoothed_array"
for (folder in folders) {dir.create(file.path(out_path, folder), showWarnings = FALSE, recursive = TRUE)}

in_folders <- list.dirs(data_path, full.names = TRUE, recursive = FALSE)

ranges <- list(c(535, 550), c(755, 780), c(755, 775), c(810, 855), c(885, 970), c(1015, 1050), c(1080, 1165), c(1225, 1285), c(1330, 1490), c(1685, 1700), c(1725, 1750), c(1780, 1960), c(1990, 2030))
range2 <- list(c(1350, 1510),c(1795, 2000), c(2320, 2500))

for (path in in_folders) {
  print(path)
  file_name <- list.files(path, pattern = "_FULL.csv", full.names = TRUE)
  for (file in file_name) {
    print(Sys.time())
    df <- read.csv(file)
    print(basename(file))
    wl <- as.numeric(sub("^X", "", names(df)))
    chunk_size <- 2000
    num_chunks <- ceiling(nrow(df) / chunk_size)
    chunks <- split(df, (seq_len(nrow(df)) - 1) %/% chunk_size)
    
    smooth_chunks <- foreach(chunk = chunks, .combine = rbind) %dopar% {
      process_chunk(chunk, wl, ranges, range2)}
  
    rownames(smooth_chunks) <- NULL
    colnames(smooth_chunks) <- as.character(wl)
    write.csv(smooth_chunks, file = paste0(out_path, "/", basename(path), "/", basename(file)), row.names = FALSE)
    stopImplicitCluster()
    rm(df)
    rm(chunks)
    rm(smooth_chunks)
   }
}