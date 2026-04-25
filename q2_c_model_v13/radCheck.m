close all;
clear all;
clc;

ambientTemp  = 305.0;
wallTemp     = ambientTemp+2.0;
sfc          = 0.0000000567;

wallNextTemp = ambientTemp;
resid        = 0.1;
history      = [resid,wallTemp];



while(resid*resid > 0.0001)
   resid = 700.0 - 7.0*(wallTemp - ambientTemp) ...
                 - 0.8*sfc*(wallTemp*wallTemp*wallTemp*wallTemp - ambientTemp*ambientTemp*ambientTemp*ambientTemp) ...
                 - ((0.05/0.007)*(wallTemp-wallNextTemp))

   wallTemp += 0.02*resid;

   history = [history;[resid,wallTemp]];

endwhile

figure(1)
   plot(history(:,1));


figure(2)
   plot(history(:,2));
