close all;
clear all;
clc;


a = dlmread("ambient25_transient.out",'',1,0);
b = dlmread("ambient35_transient.out",'',1,0);
c = dlmread("ambient45_transient.out",'',1,0);

offset = 10.0*3600.0;  % 10 hours time offset

data1 = [  000.0,21.0,22.0,23.0;
           960.0,24.0,24.0,25.0;
          2040.0,25.0,26.0,27.0;
          3000.0,27.0,28.0,29.0;
          4020.0,30.0,30.0,32.0;
          4920.0,31.0,32.0,33.0;
          5820.0,32.0,32.0,34.0;
          6120.0,32.0,32.0,34.0;
          7020.0,31.0,32.0,33.0;
          7920.0,29.0,30.0,31.0;
          8820.0,28.0,29.0,29.0;
          9720.0,26.0,27.0,28.0;
         10620.0,25.0,26.0,27.0;
         11520.0,26.0,27.0,28.0;
         12240.0,28.0,28.0,29.0;
         13320.0,29.0,29.0,30.0;
         14220.0,29.0,30.0,31.0;
         15120.0,29.0,30.0,31.0;
         16020.0,29.0,30.0,31.0;
         16920.0,31.0,31.0,33.0;
         17820.0,32.0,33.0,34.0;
         18720.0,31.0,32.0,33.0;
         19620.0,29.0,31.0,31.0;
         20520.0,28.0,29.0,30.0;
         21420.0,27.0,28.0,28.0;
         23220.0,25.0,26.0,26.0;
         25020.0,24.0,25.0,25.0];



figure(1)
   plot(a(:,2)/3600.0,a(:,36)-273.15,"linewidth",3.0,
        b(:,2)/3600.0,b(:,36)-273.15,"linewidth",3.0,
        c(:,2)/3600.0,c(:,36)-273.15,"linewidth",3.0);
%        (data1(:,1)+offset)/3600.0,data1(:,3),"linewidth",3.0,"color",'m',
%        (data1(:,1)+offset)/3600.0,data1(:,4),"linewidth",3.0,"color",'m');
   set(gca,"linewidth",2,"fontsize",36);
   grid on
   colormap jet;
   ylabel ("Temperature (degrees C)");
   xlabel ("Time (hr)");
   legend("25C Ambient, Battery T","35C Ambient, Battery T","45C Ambient, Battery T");


figure(2)
   plot(a(:,2)/3600.0,a(:,17)/1000.0,"linewidth",3.0,
        b(:,2)/3600.0,b(:,17)/1000.0,"linewidth",3.0,
        c(:,2)/3600.0,c(:,17)/1000.0,"linewidth",3.0);
   set(gca,"linewidth",2,"fontsize",36);
   grid on
   colormap jet;
   ylabel ("Power (kW)");
   xlabel ("Time (hr)");
   legend("25C Ambient, Aux Power","35C Ambient, Aux Power","45C Ambient, Aux Power");




figure(3)
   clf;
   hold on;
%   [hax, h1, h2] = plotyy (t, x, t, y);
%   [~, h3, h4] = plotyy (t+1, x, t+1, y);
## set ([h3, h4], "linestyle", "--");
## xlabel (hax(1), "xlabel");
## title (hax(2), 'Two plotyy graphs on same figure using "hold on"');
## ylabel (hax(1), "Left axis is Blue");
## ylabel (hax(2), "Right axis is Orange");
   [ax,h1,h2] = plotyy(a(:,2)/3600.0,a(:,36)-273.15,"linewidth",3.0,
                       b(:,2)/3600.0,b(:,36)-273.15,"linewidth",3.0,
                       c(:,2)/3600.0,c(:,36)-273.15,"linewidth",3.0);
   [~,h3] = plotyy(a(:,2)/3600.0,a(:,4));
   set(ax(1),"linewidth",2.0,"fontsize",20);
   set(ax(2),"linewidth",2.0,"fontsize",20);
   set(h1,"linewidth",3.0);
   set(h2,"linewidth",3.0);
   set(ax(2),"YLim",([0.0 1.1]));
   %set(ax(2),"linewidth",3.0,"fontsize",20);
   grid on
   colormap jet;
   ylabel(ax(1),"Temperature (degrees C)");
   ylabel(ax(2),"SOC");
   xlabel("Time (hr)");

