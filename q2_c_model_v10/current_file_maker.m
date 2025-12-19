close all;
clear all;
clc;

asdf = dlmread("newHill_arbitrageProfile.csv",',',1,0);

f = fopen("newHill_arbitrageCurrent.in","w");

for(i=1:size(asdf)(1))
   fprintf(f,"%f %f\n",asdf(i,1),asdf(i,3));


endfor
