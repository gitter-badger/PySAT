# -*- coding: utf-8 -*-
"""
Created on Fri Sep  2 11:31:46 2016

@author: rbanderson
"""
import numpy as np
import pysat.spectral.within_range as within_range
from sklearn.cross_decomposition.pls_ import PLSRegression
from sklearn.decomposition import PCA, FastICA
from sklearn.gaussian_process import GaussianProcess
from sklearn.linear_model import RANSACRegressor as RANSAC
import sklearn.linear_model as linear
import sklearn.svm as svm
import sklearn.kernel_ridge as kernel_ridge
from pysat.spectral.meancenter import meancenter
import scipy.optimize as opt
from pysat.plotting import plots 
import copy


class regression:
    def __init__(self,method,yrange,params,i=0,ransacparams={}):
        self.method=method 
        self.outliers=None
        self.inliers=None
        self.ransac=False
        self.yrange=yrange[i]
        
        if self.method[i]=='PLS':
            self.model=PLSRegression(**params[i])
        if self.method[i]=='OLS':
            self.model=linear.LinearRegression(**params[i])
        if self.method[i]=='OMP':
            #check whether to do CV or not
            self.do_cv=params[i]['CV']
            # create a temporary set of parameters
            params_temp = copy.copy(params[i])
            # Remove CV parameter
            params_temp.pop('CV')
            if self.do_cv is False:
                self.model=linear.OrthogonalMatchingPursuit(**params_temp)
            else:
                params_temp.pop('n_nonzero_coefs')
                self.model=linear.OrthogonalMatchingPursuitCV(**params_temp)

        if self.method[i]=='Lasso':
            # check whether to do CV or not
            self.do_cv = params[i]['CV']
            # create a temporary set of parameters
            params_temp = copy.copy(params[i])
            # Remove CV parameter
            params_temp.pop('CV')
            if self.do_cv is False:
                self.model = linear.Lasso(**params_temp)
            else:
                params_temp.pop('alpha')
                self.model = linear.LassoCV(**params_temp)


        if self.method[i]=='Elastic Net':
            # check whether to do CV or not
            self.do_cv = params[i]['CV']
            # create a temporary set of parameters
            params_temp = copy.copy(params[i])
            # Remove CV parameter
            params_temp.pop('CV')
            if self.do_cv is False:
                self.model = linear.ElasticNet(**params_temp)
            else:
                params_temp.pop('alpha')
                self.model = linear.ElasticNetCV(**params_temp)

        if self.method[i]=='Ridge':
            # check whether to do CV or not
            self.do_cv = params[i]['CV']
            # create a temporary set of parameters
            params_temp = copy.copy(params[i])
            # Remove CV parameter
            params_temp.pop('CV')
            if self.do_cv is False:
                self.model = linear.Ridge(**params_temp)
            else:
                #Ridge requires a specific set of alphas to be provided... this needs more work to be implemented correctly
                self.model = linear.RidgeCV(**params_temp)

        if self.method[i]=='Bayesian Ridge':
            self.model=linear.BayesianRidge(**params[i])
        if self.method[i]=='ARD':
            self.model=linear.ARDRegression(**params[i])
        if self.method[i]=='LARS':
            # check whether to do CV or not
            self.do_cv = params[i]['CV']
            # create a temporary set of parameters
            params_temp = copy.copy(params[i])
            # Remove CV parameter
            params_temp.pop('CV')
            if self.do_cv is False:
                self.model = linear.Lars(**params_temp)
            else:
                self.model = linear.LarsCV(**params_temp)

        if self.method[i]=='Lasso LARS':
            # check whether to do CV or not
            self.do_cv = params[i]['CV']
            # check whether to do IC or not
            self.do_ic = params[i]['IC']
            # create a temporary set of parameters
            params_temp = copy.copy(params[i])
            # Remove CV and IC parameter
            params_temp.pop('CV')
            params_temp.pop('IC')
            if self.do_cv is False and self.do_ic is False:
                self.model = linear.LassoLars(**params[i])
            if self.do_cv is True and self.do_ic is False:
                self.model = linear.LassoLarsCV(**params[i])
            if self.do_cv is False and self.do_ic is True:
                self.model = linear.LassoLarsIC(**params[i])
            if self.do_cv is True and self.do_ic is True:
                print("Can't use both cross validation AND information criterion to optimize!")

        if self.method[i]=='SVR':
            self.model=svm.SVR(**params[i])
        if self.method[i]=='KRR':
            self.model=kernel_ridge.KernelRidge(**params[i])

        if self.method[i]=='GP':
            #get the method for dimensionality reduction and the number of components
            self.reduce_dim=params[i]['reduce_dim']
            self.n_components=params[i]['n_components']
            #create a temporary set of parameters            
            params_temp=copy.copy(params[i])
            #Remove parameters not accepted by Gaussian Process
            params_temp.pop('reduce_dim')
            params_temp.pop('n_components')
            self.model=GaussianProcess(**params_temp)
#TODO: Why doesn't this if statement work correctly?            
#        if bool(ransacparams[i]):
#            print('RANSAC')
#            self.model=RANSAC(self.model,**ransacparams[i])
#            self.ransac=True
            
        
    def fit(self,x,y,i=0):
        #if gaussian processes are being used, data dimensionality needs to be reduced before fitting        
        if self.method[i]=='GP':
            if self.reduce_dim=='ICA':
                print('Reducing dimensionality with ICA')
                do_ica=FastICA(n_components=self.n_components)
                self.do_reduce_dim=do_ica.fit(x)
            if self.reduce_dim=='PCA':
                print('Reducing dimensionality with PCA')                
                do_pca=PCA(n_components=self.n_components)
                self.do_reduce_dim=do_pca.fit(x)
            x=self.do_reduce_dim.transform(x)
        try:
            print('Training model...') 
            
            self.model.fit(x,y)
        
            if self.ransac:
                self.outliers=np.logical_not(self.model.inlier_mask_)
                print(str(np.sum(self.outliers))+' outliers removed with RANSAC')
        
            #if self.method[i]=='PLS' and self.ransac==False:
            #    self.calc_Qres_Lev(x)
            self.goodfit=True
        except:
            print('There was a problem with training the model!')
            self.goodfit=False  #This can happen for GP when dimensionality is reduced too much. Use try/except to handle these cases.
            
                
    def predict(self,x,i=0):
        if self.method[i]=='GP':
            x=self.do_reduce_dim.transform(x)
        print(len(x))
        return self.model.predict(x)
        
    def calc_Qres_Lev(self,x):
        #calculate spectral residuals
        E=x-np.dot(self.model.x_scores_,self.model.x_loadings_.transpose())
        Q_res=np.dot(E,E.transpose()).diagonal()
        #calculate leverage                
        T=self.model.x_scores_
        leverage=np.diag(T@np.linalg.inv(T.transpose()@T)@T.transpose())
        self.leverage=leverage
        self.Q_res=Q_res        

        