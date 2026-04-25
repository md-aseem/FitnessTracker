
#include <stdio.h>


/* negative current is discharge */
/* positive current is charge    */
int main(void)
{
   double soc     = 0.30;
   double current = -10.0;
   int i,j;
                          /* SOC, charge heat (W), discharge heat (W)   */
                          /* this table is at 25 degrees C (Cell temp?) */
   double heat[21][3] = {{0.00,-2667.25,6427.67},
                         {0.05,-1654.31,2938.16},
                         {0.10, 1550.37,3383.36},
                         {0.15, 1084.38,3471.15},
                         {0.20,  703.30,3483.69},
                         {0.25, 1074.51,2580.74},
                         {0.30, 1779.42, 906.53},
                         {0.35, 3230.71, 266.94},
                         {0.40, 3315.61,  38.07},
                         {0.45, 3522.94, -15.23},
                         {0.50, 3434.09,  78.83},
                         {0.55, 3412.37, 389.22},
                         {0.60, 3337.33,1028.80},
                         {0.65, 2336.24,1740.50},
                         {0.70, 1526.68,1840.83},
                         {0.75, 1453.62,1765.58},
                         {0.80, 1751.78,1649.58},
                         {0.85, 1793.24,1568.06},
                         {0.90, 1801.14,1401.89},
                         {0.95, 1751.78,1260.81},
                         {1.00, 3708.64,-335.05}};

   for(i=0;i<21;i++){  if((soc >= heat[i][0]) && (soc < heat[i+1][0])){  printf(" found %f >= %f\n",soc,heat[i][0]);  break; } }

   printf(" i = %i\n",i);

   /* get charge or discharge index */
   if(current <= -0.01)   j = 2;
   if(current >=  0.01)   j = 1;
   if((current > -0.01) && (current < 0.01)) return 0;   /* if the current is zero */


   printf(" %f\n",heat[i][j] + ((heat[i+1][j] - heat[i][j])/0.05)*(soc-heat[i][0]));

   return 0;
}

