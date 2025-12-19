close all;
clear all;
clc;

m     = 35.0;            % mass of PDU, kg
Tcold = 273.15 - 40.0;

T     = 273.15 + 20.0;   % K, initial temperature of the pdu

pducp = 35.0*385.0;
t     = 0.0;
tmax  = 3600.0*4.0;
dt    = 0.25;

history = [t,T];

while t < tmax

   T += 4.0*(Tcold - T)*dt/(pducp);

   history = [history;t,T];

   t += dt;

endwhile


figure(1)
   plot(history(:,1)/3600.0,history(:,2)-273.15);
