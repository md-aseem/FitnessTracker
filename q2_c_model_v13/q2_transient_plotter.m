close all;
clear all;
clc;

a = dlmread("transient.out",'',1,0);

offset = 10.1*3600.0;  % 10 hours time offset

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
   plot(a(:,2)/3600.0,a(:,26)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,27)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,28)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,29)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,30)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,36)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,42)-273.15,"linewidth",3.0);
%        (data1(:,1)+offset)/3600.0,data1(:,3),"linewidth",3.0,"color",'m',
%        (data1(:,1)+offset)/3600.0,data1(:,4),"linewidth",3.0,"color",'m');
   set(gca,"linewidth",2,"fontsize",30);
   grid on
   colormap jet;
   ylabel ("Temperature (degrees C)");
   xlabel ("Time (hr)");
   legend("ambient T","internal Air T","Coolant Leaving Chiller Temp","Coolant Entering Chiller Temp","B[0] T","B[6] T","Outer Wall Temp");

figure(2)
   subplot(2,1,1);
      plot(a(:,2)/3600.0,a(:,26)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,27)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,28)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,29)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,30)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,36)-273.15,"linewidth",3.0);
   set(gca,"linewidth",2,"fontsize",20);
   grid on
   colormap jet;
   ylabel ("Temperature (degrees C)");
   xlabel ("Time (hr)");
   legend("ambient T","internal Air T","Coolant Leaving Chiller Temp","Coolant Entering Chiller Temp","B[0] T","B[6] T");

   subplot(2,1,2);
   plot(%a(:,2)/3600.0,a(:,5),"linewidth",3.0,
        a(:,2)/3600.0,a(:,11),"linewidth",3.0,
        a(:,2)/3600.0,a(:,9),"linewidth",3.0);
%   [ax2,h2_1,h2_2] = plotyy(a(:,2)/3600.0,a(:,5),"linewidth",3.0,
%                           [a(:,2)/3600.0,a(:,11),"linewidth",3.0,
%                            a(:,2)/3600.0,a(:,13),"linewidth",3.0,
%                            a(:,2)/3600.0,a(:,9),"linewidth",3.0]);
   set(gca,"linewidth",2,"fontsize",20);
   grid on
   colormap jet;
   ylabel ("Control Setting");
   xlabel ("Time (hr)");
   %legend("Chiller Mode Index","Bat Pump Pcnt","PCS Pump Pcnt","Compressor Pcnt");
   legend("Bat Pump Pcnt","Compressor Pcnt");


figure(3)
   plot(a(:,2)/3600.0,a(:,23)/1000.0,"linewidth",3.0,
        a(:,2)/3600.0,-a(:,24)/1000.0,"linewidth",3.0,
        a(:,2)/3600.0,a(:,17)/1000.0,"linewidth",3.0,
        a(:,2)/3600.0,a(:,41)/1000.0,"linewidth",3.0);
   set(gca,"linewidth",2,"fontsize",32);
   grid on
   colormap jet;
   ylabel ("Flux (kW)");
   xlabel ("Time (hr)");
   legend("Battery Heat","Cold Plate Flux","Aux Power","Solar Radiation Load");
%   legend("Aux Power","Solar Radiation Load");

figure(4)
   [ax,h1,h2] = plotyy(a(:,2)/3600.0,a(:,3),
                       a(:,2)/3600.0,a(:,4));
   set(ax(1),"linewidth",2.0,"fontsize",20);
   set(ax(2),"linewidth",2.0,"fontsize",20);
   set(h1,"linewidth",3.0);
   set(h2,"linewidth",3.0);
   set(ax(2),"YLim",([0.0 1.1]));
   %set(ax(2),"linewidth",3.0,"fontsize",20);
   grid on
   colormap jet;
   ylabel(ax(1),"Cell Current (A)");
   ylabel(ax(2),"SOC");
   xlabel("Time (hr)");

figure(5)
   plot(a(:,2)/3600.0,a(:,22),"linewidth",3.0,
        a(:,2)/3600.0,a(:,39),"linewidth",3.0,
        a(:,2)/3600.0,a(:,40),"linewidth",3.0);
   set(gca,"linewidth",2,"fontsize",20);
   grid on
   colormap jet;
   ylabel ("Cumulative Aux Energy (kW*hr)");
   xlabel ("Time (hr)");
   l = legend("Aux Energy","Cumulative Battery Heat","Ambient Energy Exchange");
   legend(l,"location","northwest");


figure(6)
   plot(%a(:,2)/3600.0,a(:,30)-273.15,"linewidth",3.0,
        a(:,2)/3600.0,a(:,36)-273.15,"linewidth",3.0,"color",'r',
        (data1(:,1)+offset)/3600.0,data1(:,3),"linewidth",3.0,"color",[0.6,0.6,0.6],"linestyle","--",
        (data1(:,1)+offset)/3600.0,data1(:,4),"linewidth",3.0,"color",[0.6,0.6,0.6],"linestyle","--");
   set(gca,"linewidth",2,"fontsize",32);
   grid on
   colormap jet;
   ylabel ("Temperature (degrees C)");
   xlabel ("Time (hr)");
%   legend("B[0] T","B[6] T","Test Ave T","Test Max T");
   legend("Simulation Max Battery T","Test Ave T","Test Max T");
   axis([9.0 19.0 20.0 36.0]);

figure(7)
   plot(a(:,2)/3600.0,a(:,17)/1000.0,"linewidth",3.0);
   set(gca,"linewidth",2,"fontsize",20);
   grid on
   colormap jet;
   ylabel ("Aux Power (kW)");
   xlabel ("Time (hr)");
%   legend("Aux Power","Solar Radiation Load");

figure(8)
   plot(a(:,2)/3600.0,a(:,4),"linewidth",3.0);
   %set(ax(2),"linewidth",3.0,"fontsize",20);
   set(gca,"linewidth",2,"fontsize",20);
   grid on
   colormap jet;
   ylabel("SOC");
   xlabel("Time (hr)");

