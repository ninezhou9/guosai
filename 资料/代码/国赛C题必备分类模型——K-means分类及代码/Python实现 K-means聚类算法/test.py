from numpy import *  
import time  
import matplotlib.pyplot as plt  
import kmeans
  
## step 1: load data  
print "step 1: load data..."  
dataSet = []  
fileIn = open('data.txt')  
for line in fileIn.readlines():  
    lineArr = line.strip().split('\t')  
    dataSet.append([float(lineArr[0]), float(lineArr[1])])  
  
## step 2: clustering...  
print "step 2: clustering..."  
dataSet = mat(dataSet)  
k = 2  
centroids, clusterAssment = kmeans.kmeans(dataSet, k)  
  
## step 3: show the result  
print "step 3: show the result..."  
kmeans.showCluster(dataSet, k, centroids, clusterAssment)  