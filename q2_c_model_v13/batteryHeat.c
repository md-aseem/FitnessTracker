
#include "data_structures.h"
#include "preprocess.h"
#include <stdio.h>


/* negative current is discharge */
/* positive current is charge    */
double batteryTotalHeatGeneration(struct SimMain *simmain)
{
   struct Chiller *c = chillerListHead;
   struct Battery *b = batteryListHead;
   double h1,h2;
   int i,j = -99999;
                          /* SOC, charge heat (W), discharge heat (W)   */
                          /* this table is at 25 degrees C (Cell temp?) */
                          /* soc   0.50DP    0.25DP     0        0.25CP  0.50CP */
                          /*        -150A     -75A      0A         75A    150A  */
                          /* updated for Q2 CATL306 cells at BOL on October 10 2025 */
/*   double heat[22][6] = {{0.00,    -150.00,   -75.00, 0.00000,    75.00,   150.00},
                         {0.00,    8000.00,  3300.00, 0.00000,  2500.00,  5400.00},
                         {0.05,    7142.72,  2857.92, 0.00000,  1697.28,  4767.36},
                         {0.15,    4850.56,  1926.08, 0.00000,  1518.40,  3931.20},
                         {0.25,    4858.88,  1917.76, 0.00000,  1593.28,  3981.12},
                         {0.35,    4496.96,  1776.32, 0.00000,    1439.36,  3702.40},
                         {0.45,    3877.12,  1535.04, 0.00000,  1501.76,  3931.20},
                         {0.55,    3972.80,  1609.92, 0.00000,  1576.64,  4114.24},
                         {0.65,    4746.56,  1838.72, 0.00000,  1418.56,  3490.24},
                         {0.75,    4089.28,  1485.12, 0.00000,  1555.84,  3885.44},
                         {0.85,    3785.60,  1347.84, 0.00000,  1776.32,  4480.32},
                         {0.95,    3752.32,  1343.68, 0.00000,  2304.64,  5894.72},
                         {1.00,    3900.00,  1700.00, 0.00000,  2800.00,  6300.00}};
*/


   /* determine what row to refer to                              */
   /* skip the first row because that's the current not the power */
   if(b->soc > ONE) { printf(" WARNING:  SOC exceeded 100%%, capping at 100%%\n");  b->soc = ONE;  }
   if(b->soc < ZERO){ printf(" WARNING:  SOC is below 0%%, capping at 0%%\n");      b->soc = ZERO; }

   for(i=1;i<21;i++){  if((b->soc >= heat(i,0)) && (b->soc < heat(i+1,0)))   break;  }



   /* calculate the columns to go between                         */
   /* skip the first column because that's the soc                */
   if(currentCurrent < heat(0,1)){ j = 1; }
   if(currentCurrent > heat(0,5)){ j = 4; }
   if(j < -9999){  for(j=1;j<5;j++){  if((currentCurrent >= heat(0,j)) && (currentCurrent < heat(0,j+1))) break;  }   }


   /* get the  */
   h1 = heat(i,j)   + (currentCurrent - heat(0,j))*(heat(i,j+1) - heat(i,j))/(heat(0,j+1) - heat(0,j));
   h2 = heat(i+1,j) + (currentCurrent - heat(0,j))*(heat(i+1,j+1) - heat(i+1,j))/(heat(0,j+1) - heat(0,j));


   /* this is the latest implementation to go across the table */
//   return (b->bol_eol)*(152.0/157.0)*10.0*(h1 + (soc-heat[i][0])*(h2-h1)/(heat[i+1][0]-heat[i][0]));
//   printf("cell heat -> %e W, total battery heat -> %e W\n",(h1 + (b->soc-heat(i,0))*(h2-h1)/(heat(i+1,0)-heat(i,0))),
//   (simmain->bol_eol)*(simmain->cellsPerModule)*(simmain->modulesPerQuantum)*(h1 + (b->soc-heat(i,0))*(h2-h1)/(heat(i+1,0)-heat(i,0))));
   return (simmain->bol_eol)*(simmain->cellsPerModule)*(simmain->modulesPerQuantum)*(h1 + (b->soc-heat(i,0))*(h2-h1)/(heat(i+1,0)-heat(i,0)));
}


double cellOCV(struct SimMain *simmain)
{
   struct Battery *b = batteryListHead;
   int i;

   if((b->soc) > ONE) { printf(" WARNING:  SOC exceeded 100%%, capping at 100%%\n"); } //  soc = ONE;  }
   if((b->soc) < ZERO){ printf(" WARNING:  SOC is below 0%%, capping at 0%%\n");     } // soc = ZERO; }

   //for(i=0;i<29;i++){  if(((b->soc) >= ocv[i][0]) && ((b->soc) < ocv[i+1][0]))   break;  }
   for(i=0;i<29;i++){  if(((b->soc) >= b->ocv[i][0]) && ((b->soc) < b->ocv[i+1][0]))   break;  }

   //return (ocv[i][1]   + ((b->soc) - ocv[i][0])*(ocv[i+1][1] - ocv[i][1])/(ocv[i+1][0] - ocv[i][0]));
   return (b->ocv[i][1]   + ((b->soc) - b->ocv[i][0])*(b->ocv[i+1][1] - b->ocv[i][1])/(b->ocv[i+1][0] - b->ocv[i][0]));
}

