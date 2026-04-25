close all;
clear all;
clc;


function asdf = aux_cp(tc)
   b0  =  4498.5;
   b1  = -129.24938;
   b2  =  105.74901;
   b3  = -4.02737605;
   b4  =  3.29419546;
   b5  =  1.91560796;
   b6  = -0.017065623;
   b7  =  0.031504817;
   b8  =  0.0180438548;
   b9  = -0.0101275759;

   te = 15.0;

   asdf = (b0 + b1*te       ...
              + b2*tc       ...
              + b3*te*te    ...
              + b4*te*tc    ...
              + b5*tc*tc    ...
              + b6*te*te*te ...
              + b7*te*te*tc ...
              + b8*te*tc*tc ...
              + b9*tc*tc*tc);
endfunction


function asdf = capacity_cp(tc)
   b0  =  51258.1944;
   b1  =   1728.89617;
   b2  = -341.739630;
   b3  =  22.6776144;
   b4  = -10.1623021;
   b5  =  0.404030283;
   b6  =  0.104336561;
   b7  = -0.131153764;
   b8  = -0.00913508805;
   b9  = -0.00712386496;

   te = 15.0;

   asdf = (b0 + b1*te       ...
              + b2*tc       ...
              + b3*te*te    ...
              + b4*te*tc    ...
              + b5*tc*tc    ...
              + b6*te*te*te ...
              + b7*te*te*tc ...
              + b8*te*tc*tc ...
              + b9*tc*tc*tc);
endfunction



tcr = 20.0:2.0:70.0;

for i=1:1:25
   data(i,1) = 20.0 + 2.0*(i-1);
   data(i,2) = aux_cp(data(i,1));
   data(i,3) = capacity_cp(data(i,1));
endfor


figure(1)
   plot(data(:,1),data(:,2),"linewidth",3.0,
        data(:,1),data(:,3),"linewidth",3.0);
   set(gca,"linewidth",2,"fontsize",20);
   grid on
   colormap jet;
