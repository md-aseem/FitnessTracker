close all;
clear all;
clc;

function asdf = y(a)
   asdf = 350.0*(1.0-(a*a)/(7.0*7.0));
endfunction


for i = 1:1:56
   x = -7.0 + 0.25*i;

   data(i,1) = x;
   data(i,2) = y(x);
endfor


figure(1)
   plot(data(:,1),data(:,2));
