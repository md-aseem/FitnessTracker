

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "data_structures.h"
#include "preprocess.h"


void tellAboutTheCycles(struct SimMain *simmain);
void setCRate(struct SimMain *simmain);
void loadChillerCurves(struct SimMain *simmain);
void loadBatteryCurves(struct SimMain *simmain);
void setupHvac(struct SimMain *simmain);


void housekeeping(struct SimMain *simmain)
{
   struct Battery     *b   = batteryListHead;
   struct CDCycle     *cyc = cycleListHead;
   struct ThermalWall *w1  = simmain->tw1;
   struct ThermalWall *w2  = simmain->tw2;
   int i;


   tellAboutTheCycles(simmain);


   simmain->cellsPerModule = 52.0;
   simmain->modulesPerQuantum = 80.0;

   fprintf(LOGFILE,"\n This run is for Quantum 2.0\n");
   fprintf(LOGFILE," There are %3.0f cells per module, and %3.0f modules inside the Quantum\n\n",simmain->cellsPerModule,simmain->modulesPerQuantum);


   /* a bunch of kind of random assignments we have to do */
   for(i=0;i<7;i++){  b->temperature[i] = simmain->initialTemperature;
                      b->tempLast[i]    = simmain->initialTemperature; }

   /* start the run with a linear temperature distribution across the wall thickness */
   for(i=0;i<7;i++)  w1->temp[i]     = nextT_internal + ((simmain->ambientTemperature - nextT_internal)/7.0)*i;
   for(i=0;i<7;i++)  w1->tempLast[i] = nextT_internal + ((simmain->ambientTemperature - nextT_internal)/7.0)*i;

   for(i=0;i<7;i++)  w2->temp[i]     = nextT_internal + ((simmain->ambientTemperature - nextT_internal)/7.0)*i;
   for(i=0;i<7;i++)  w2->tempLast[i] = nextT_internal + ((simmain->ambientTemperature - nextT_internal)/7.0)*i;


   if((simmain->sunriseTime < -998.0) || (simmain->sunsetTime < -998.0))
   {
      fprintf(LOGFILE," No solar radiation model will be used in this run\n");
      fprintf(LOGFILE," To use a solar radiation model, call out sunrise and sunset times\n");
      fprintf(LOGFILE," using @SUNRISE_TIME{  } and @SUNSET_TIME{ }\n\n");
      simmain->radiationModelOnOrOff = OFF;
   }


   /* set battery heat generation beginning of life / end of life factor */
   if(strcmp("beginning_of_life",simmain->batteryLifeStatus) == 0)  simmain->bol_eol = ONE;
   if(strcmp("end_of_life",simmain->batteryLifeStatus) == 0)   simmain->bol_eol = 1.30000000;
   if(simmain->bol_eol < -998.0)
   {
      simmain->bol_eol = ONE;  /* use one unless something is specified */
      fprintf(LOGFILE,"\n No BOL or EOL condition was specified in the input file \n");
      fprintf(LOGFILE,"   A Beginning-of-Life state will be considered\n"); 
   }


   setCRate(simmain);


   loadChillerCurves(simmain);


   loadBatteryCurves(simmain);


   setupHvac(simmain);


   return ;
}


void setCRate(struct SimMain *simmain)
{
   struct Battery *b = batteryListHead;

   simmain->cRate =  TOTAL_SYSTEM_ENERGY*simmain->cRate*MEGAWATTS_TO_WATTS;
   simmain->dRate = -TOTAL_SYSTEM_ENERGY*simmain->dRate*MEGAWATTS_TO_WATTS;

   return ;
}



void tellAboutTheCycles(struct SimMain *simmain)
{
   struct CDCycle *cyc = cycleListHead;
   struct Battery *b   = batteryListHead;
   double startingSoc  = b->soc;
   double lastEndTime  = NO_INPUT;
   int i = 1;


   if((startingSoc < ZERO) || (startingSoc > ONE))
   {
      fprintf(LOGFILE,"\n\n Error! The starting SOC value is %f !\n",startingSoc);
      fprintf(LOGFILE," This is outside of the allowable range for SOC\n");
      fprintf(LOGFILE," The SOC must be between 0 and 1!  Exiting\n\n");

      exit(1);
   }


   while(cyc != NULL)
   {
      /* at this stage, the c  */
      if(startingSoc <= cyc->targetSoc1)     cyc->power1 =  TOTAL_SYSTEM_ENERGY*maxChargeRate*MEGAWATTS_TO_WATTS;
      if(startingSoc >  cyc->targetSoc1)     cyc->power1 = -TOTAL_SYSTEM_ENERGY*maxDischargeRate*MEGAWATTS_TO_WATTS;

      if(cyc->targetSoc1 <= cyc->targetSoc2) cyc->power2 =  TOTAL_SYSTEM_ENERGY*maxChargeRate*MEGAWATTS_TO_WATTS;
      if(cyc->targetSoc1 >  cyc->targetSoc2) cyc->power2 = -TOTAL_SYSTEM_ENERGY*maxDischargeRate*MEGAWATTS_TO_WATTS;


      cyc->endTime1   = cyc->startTime  + (cyc->targetSoc1 - startingSoc)/(cyc->power1 / (TOTAL_SYSTEM_ENERGY*MEGAWATTS_TO_WATTS));
      cyc->startTime2 = cyc->endTime1   + cyc->waitTime;
      cyc->endTime2   = cyc->startTime2 + (cyc->targetSoc2 - cyc->targetSoc1)/(cyc->power2 / (TOTAL_SYSTEM_ENERGY*MEGAWATTS_TO_WATTS));


      fprintf(LOGFILE," --- CHARGE-DISCHARGE CYCLE %i ---\n",i);
      fprintf(LOGFILE,"     part 1 starts at:     %6.2f hours\n",cyc->startTime);   cyc->startTime  = cyc->startTime*CONVERT_HOURS_TO_SECONDS;
      fprintf(LOGFILE,"     part 1 ends   at:     %6.2f hours\n",cyc->endTime1);    cyc->endTime1   = cyc->endTime1*CONVERT_HOURS_TO_SECONDS;
      fprintf(LOGFILE,"     part 2 starts at:     %6.2f hours\n",cyc->startTime2);  cyc->startTime2 = cyc->startTime2*CONVERT_HOURS_TO_SECONDS;
      fprintf(LOGFILE,"     part 2 ends   at:     %6.2f hours\n",cyc->endTime2);    cyc->endTime2   = cyc->endTime2*CONVERT_HOURS_TO_SECONDS;


      /* make sure that this cycle doesn't start before the last cycle ends */
      if((NEXT(cyc) != NULL) && (NEXT(cyc)->startTime < (cyc->endTime2/CONVERT_HOURS_TO_SECONDS)))
      {
         printf(" in here\n");
         fprintf(LOGFILE," Warning!  Cycle %i is supposed to begin before the last\n",i+1);
         fprintf(LOGFILE," cycle ends.  Cycle %i will be ignored\n",i+1);
         NEXT(cyc) = NULL;
         break;
      }

      startingSoc = cyc->targetSoc2;

      cyc = NEXT(cyc);   i += 1;
   }


   return ;
}



void loadChillerCurves(struct SimMain *simmain)
{
   struct Chiller *c = chillerListHead;
   double ac, cc, nk;   /* coefficients for a cap on aux power, cap on compressor %, and due to noise kit */
   int i;

   if((strcmp("envicool_55kW_c/2",simmain->chillerModelName) == 0) || (strcmp("envicool_55kW_c/4",simmain->chillerModelName) == 0))
   {
      fprintf(LOGFILE," Using the Envicool 55kW Chiller\n\n");

      c->coolingPowerCoeff = ONE;
      c->compAuxCap        = 0.95;
      c->pumpAuxCap        = 0.93;

      if(strcmp("envicool_55kW_c/4",simmain->chillerModelName) == 0){fprintf(LOGFILE," applying 0.25C chiller caps\n");
                                                                     c->pumpAuxCap        = 0.52;
                                                                     c->compAuxCap        = 0.71; 
                                                                     c->coolingPowerCoeff = 0.818;      } 

      cc = c->coolingPowerCoeff;
      ac = 0.70*c->compAuxCap + 0.15*c->pumpAuxCap + 0.15;
      nk = ONE;
      fprintf(LOGFILE," The Noise kit is not present, the input does not change this\n");


      /*                                         */
      /*              QUANTUM 2.0                */
      /*     55kW  ENVICOOL CHILLER TABLES       */
      /*                                         */
                           /* ambient temp */  /* cooling power @ 18C */       /* compressor power @ 18C */
      c->cooling18[0][0]   = (-30.0 + 273.15);   c->cooling18[0][1]  = cc*70500.0;    c->cooling18[0][2]  = ac*16250.0;
      c->cooling18[1][0]   = (-10.0 + 273.15);   c->cooling18[1][1]  = cc*70500.0;    c->cooling18[1][2]  = ac*16250.0;
      c->cooling18[2][0]   = ( 00.0 + 273.15);   c->cooling18[2][1]  = cc*70500.0;    c->cooling18[2][2]  = ac*16250.0;
      c->cooling18[3][0]   = ( 05.0 + 273.15);   c->cooling18[3][1]  = cc*69000.0;    c->cooling18[3][2]  = ac*16500.0;
      c->cooling18[4][0]   = ( 15.0 + 273.15);   c->cooling18[4][1]  = cc*68000.0;    c->cooling18[4][2]  = ac*17500.0;
      c->cooling18[5][0]   = ( 20.0 + 273.15);   c->cooling18[5][1]  = cc*65000.0;    c->cooling18[5][2]  = ac*18000.0;
      c->cooling18[6][0]   = ( 25.0 + 273.15);   c->cooling18[6][1]  = cc*62500.0;    c->cooling18[6][2]  = ac*18500.0;
      c->cooling18[7][0]   = ( 30.0 + 273.15);   c->cooling18[7][1]  = cc*58000.0;    c->cooling18[7][2]  = ac*20000.0;
      c->cooling18[8][0]   = ( 35.0 + 273.15);   c->cooling18[8][1]  = cc*55000.0;    c->cooling18[8][2]  = ac*22000.0;
      c->cooling18[9][0]   = ( 40.0 + 273.15);   c->cooling18[9][1]  = cc*51000.0;    c->cooling18[9][2]  = ac*23500.0;
      c->cooling18[10][0]  = ( 45.0 + 273.15);   c->cooling18[10][1] = cc*46500.0;    c->cooling18[10][2] = ac*22500.0;
      c->cooling18[11][0]  = ( 50.1 + 273.15);   c->cooling18[11][1] = cc*30500.0;    c->cooling18[11][2] = ac*17500.0;

                        /* ambient temp */  /* cooling power @ 23C */       /* compressor power @ 23C */
      c->cooling23[0][0]   = (-30.0 + 273.15);   c->cooling23[0][1]  = cc*72500.0;    c->cooling23[0][2]  = ac*15750.0;
      c->cooling23[1][0]   = (-10.0 + 273.15);   c->cooling23[1][1]  = cc*72500.0;    c->cooling23[1][2]  = ac*15750.0;
      c->cooling23[2][0]   = ( 00.0 + 273.15);   c->cooling23[2][1]  = cc*72500.0;    c->cooling23[2][2]  = ac*15750.0;
      c->cooling23[3][0]   = ( 05.0 + 273.15);   c->cooling23[3][1]  = cc*71000.0;    c->cooling23[3][2]  = ac*16000.0;
      c->cooling23[4][0]   = ( 15.0 + 273.15);   c->cooling23[4][1]  = cc*70000.0;    c->cooling23[4][2]  = ac*17000.0;
      c->cooling23[5][0]   = ( 20.0 + 273.15);   c->cooling23[5][1]  = cc*67000.0;    c->cooling23[5][2]  = ac*17500.0;
      c->cooling23[6][0]   = ( 25.0 + 273.15);   c->cooling23[6][1]  = cc*64500.0;    c->cooling23[6][2]  = ac*18000.0;
      c->cooling23[7][0]   = ( 30.0 + 273.15);   c->cooling23[7][1]  = cc*60000.0;    c->cooling23[7][2]  = ac*19500.0;
      c->cooling23[8][0]   = ( 35.0 + 273.15);   c->cooling23[8][1]  = cc*57000.0;    c->cooling23[8][2]  = ac*21500.0;
      c->cooling23[9][0]   = ( 40.0 + 273.15);   c->cooling23[9][1]  = cc*53000.0;    c->cooling23[9][2]  = ac*23000.0;
      c->cooling23[10][0]  = ( 45.0 + 273.15);   c->cooling23[10][1] = cc*48500.0;    c->cooling23[10][2] = ac*22000.0;
      c->cooling23[11][0]  = ( 50.1 + 273.15);   c->cooling23[11][1] = cc*32500.0;    c->cooling23[11][2] = ac*17000.0;
   }
   else if((strcmp("bergstrom_55kW_c/2",simmain->chillerModelName) == 0) || 
           (strcmp("bergstrom_55kW_c/4",simmain->chillerModelName) == 0) ||
           (strcmp("bergstrom_55kW_c/8",simmain->chillerModelName) == 0))
   {
      fprintf(LOGFILE," Using the Bergstrom 55kW Chiller\n\n");

      c->coolingPowerCoeff = ONE;
      c->compAuxCap        = 0.95;
      c->pumpAuxCap        = 0.93;

      if(strcmp("bergstrom_55kW_c/4",simmain->chillerModelName) == 0){fprintf(LOGFILE," applying 0.25C chiller caps\n");
                                                                     c->pumpAuxCap        = 0.52;
                                                                     c->compAuxCap        = 0.71; 
                                                                     c->coolingPowerCoeff = 0.818;      } 

      if(strcmp("bergstrom_55kW_c/8",simmain->chillerModelName) == 0){fprintf(LOGFILE," applying 0.125C chiller caps\n");
                                                                     c->pumpAuxCap        = 0.52;
                                                                     c->compAuxCap        = 0.50; 
                                                                     c->coolingPowerCoeff = 0.55;      } 

      cc = c->coolingPowerCoeff;
      ac = 0.70*c->compAuxCap + 0.15*c->pumpAuxCap + 0.15;
      nk = ONE;

      fprintf(LOGFILE," The Noise kit is not present, the input does not change this\n");
                           /* ambient temp */  /* cooling power @ 18C */       /* compressor power @ 18C */
      c->cooling18[0][0]   = (-30.0 + 273.15);   c->cooling18[0][1]  = cc*70000.0;    c->cooling18[0][2]  = ac*13000.0;
      c->cooling18[1][0]   = (-10.0 + 273.15);   c->cooling18[1][1]  = cc*70000.0;    c->cooling18[1][2]  = ac*13000.0;
      c->cooling18[2][0]   = ( 00.0 + 273.15);   c->cooling18[2][1]  = cc*70000.0;    c->cooling18[2][2]  = ac*13000.0;
      c->cooling18[3][0]   = ( 05.0 + 273.15);   c->cooling18[3][1]  = cc*69000.0;    c->cooling18[3][2]  = ac*13000.0;
      c->cooling18[4][0]   = ( 15.0 + 273.15);   c->cooling18[4][1]  = cc*68000.0;    c->cooling18[4][2]  = ac*13200.0;
      c->cooling18[5][0]   = ( 20.0 + 273.15);   c->cooling18[5][1]  = cc*65000.0;    c->cooling18[5][2]  = ac*14800.0;
      c->cooling18[6][0]   = ( 25.0 + 273.15);   c->cooling18[6][1]  = cc*65000.0;    c->cooling18[6][2]  = ac*16800.0;
      c->cooling18[7][0]   = ( 30.0 + 273.15);   c->cooling18[7][1]  = cc*60000.0;    c->cooling18[7][2]  = ac*18800.0;
      c->cooling18[8][0]   = ( 35.0 + 273.15);   c->cooling18[8][1]  = cc*55000.0;    c->cooling18[8][2]  = ac*22200.0;
      c->cooling18[9][0]   = ( 40.0 + 273.15);   c->cooling18[9][1]  = cc*50000.0;    c->cooling18[9][2]  = ac*21700.0;
      c->cooling18[10][0]  = ( 45.0 + 273.15);   c->cooling18[10][1] = cc*38000.0;    c->cooling18[10][2] = ac*17200.0;
      c->cooling18[11][0]  = ( 50.1 + 273.15);   c->cooling18[11][1] = cc*26000.0;    c->cooling18[11][2] = ac*13200.0;

                        /* ambient temp */  /* cooling power @ 23C */       /* compressor power @ 23C */
      c->cooling23[0][0]   = (-30.0 + 273.15);   c->cooling23[0][1]  = cc*74000.0;    c->cooling23[0][2]  = ac*12740.0;
      c->cooling23[1][0]   = (-10.0 + 273.15);   c->cooling23[1][1]  = cc*74000.0;    c->cooling23[1][2]  = ac*12740.0;
      c->cooling23[2][0]   = ( 00.0 + 273.15);   c->cooling23[2][1]  = cc*74000.0;    c->cooling23[2][2]  = ac*12740.0;
      c->cooling23[3][0]   = ( 05.0 + 273.15);   c->cooling23[3][1]  = cc*73000.0;    c->cooling23[3][2]  = ac*12740.0;
      c->cooling23[4][0]   = ( 15.0 + 273.15);   c->cooling23[4][1]  = cc*72000.0;    c->cooling23[4][2]  = ac*12900.0;
      c->cooling23[5][0]   = ( 20.0 + 273.15);   c->cooling23[5][1]  = cc*69000.0;    c->cooling23[5][2]  = ac*14500.0;
      c->cooling23[6][0]   = ( 25.0 + 273.15);   c->cooling23[6][1]  = cc*66500.0;    c->cooling23[6][2]  = ac*16400.0;
      c->cooling23[7][0]   = ( 30.0 + 273.15);   c->cooling23[7][1]  = cc*62000.0;    c->cooling23[7][2]  = ac*18400.0;
      c->cooling23[8][0]   = ( 35.0 + 273.15);   c->cooling23[8][1]  = cc*59000.0;    c->cooling23[8][2]  = ac*21800.0;
      c->cooling23[9][0]   = ( 40.0 + 273.15);   c->cooling23[9][1]  = cc*52000.0;    c->cooling23[9][2]  = ac*21270.0;
      c->cooling23[10][0]  = ( 45.0 + 273.15);   c->cooling23[10][1] = cc*40000.0;    c->cooling23[10][2] = ac*16860.0;
      c->cooling23[11][0]  = ( 50.1 + 273.15);   c->cooling23[11][1] = cc*28000.0;    c->cooling23[11][2] = ac*12940.0;
   }
   else
   {
      fprintf(LOGFILE," The chiller name called out is not recognized\n");
      fprintf(LOGFILE," Recognized chiller names are:  envicool_55kW_c/4\n");
      fprintf(LOGFILE,"                                envicool_55kW_c/2\n");
      fprintf(LOGFILE,"                                bergstrom_55kW_c/4\n");
      fprintf(LOGFILE,"                                bergstrom_55kW_c/2\n");
      fprintf(LOGFILE," Exiting\n");
      exit(1);
   }

   /* report the chiller table to the log file */
   fprintf(LOGFILE," *** CHILLER PERFORMANCE TABLES ***\n\n");
   fprintf(LOGFILE,"\n     *** AT 18C COLD SIDE TEMP ***\n   Ambient Temp     Cooling       Aux Power\n");
   fprintf(LOGFILE,"   (degrees C)     Power (W)    Consumption (W)\n");
   for(i=0;i<=11;i++)  fprintf(LOGFILE,              "    %6.2f        %9.1f      %9.1f\n",c->cooling18[i][0]-273.15,c->cooling18[i][1],c->cooling18[i][2]);  
   
   fprintf(LOGFILE,"\n\n     *** AT 23C COLD SIDE TEMP ***\n   Ambient Temp     Cooling       Aux Power\n");
   fprintf(LOGFILE,"   (degrees C)     Power (W)    Consumption (W)\n");
   for(i=0;i<=11;i++)  fprintf(LOGFILE,"   %6.2f          %9.1f      %9.1f\n",c->cooling23[i][0]-273.15,c->cooling23[i][1],c->cooling23[i][2]);  
   fprintf(LOGFILE,"\n\n");

   return ;      
}



void loadBatteryCurves(struct SimMain *simmain)
{
   struct Battery *b = batteryListHead;
   int i;

   /* eve 306A*hrs, for Q2.0 */
   if(strcmp("eve_306Ahr",simmain->batteryModelName) == 0)
   {
      fprintf(LOGFILE," Using the EVE 306 A*hr battery properties\n");
      /* SOC, charge heat (W), discharge heat (W)               */
      /* this table is at 25 degrees C (Cell temp?)             */
      /* updated for Q2 EVE306 cells at BOL on December 3 2025  */
      /*            soc                 0.50DP                0.25DP                  0                 0.25CP               0.50CP    */
      heat(0,0)  = 0.00;  heat(0,1)  = -b->cellCapacityAh*0.50;  heat(0,2)  = -b->cellCapacityAh*0.25;  heat(0,3)  = ZERO;  heat(0,4)  = b->cellCapacityAh*0.25;  heat(0,5)  = b->cellCapacityAh*0.50;
      heat(1,0)  = 0.00;  heat(1,1)  =   63.05;  heat(1,2)  =  27.43;  heat(1,3)  = ZERO;  heat(1,4)  = 27.95;  heat(1,5)  =  10.54;
      heat(2,0)  = 0.05;  heat(2,1)  =   38.80;  heat(2,2)  =  16.07;  heat(2,3)  = ZERO;  heat(2,4)  =  6.96;  heat(2,5)  =  19.45;
      heat(3,0)  = 0.10;  heat(3,1)  =   14.54;  heat(3,2)  =   4.71;  heat(3,3)  = ZERO;  heat(3,4)  =  3.38;  heat(3,5)  =  10.95;
      heat(4,0)  = 0.20;  heat(4,1)  =   13.31;  heat(4,2)  =   4.07;  heat(4,3)  = ZERO;  heat(4,4)  =  3.25;  heat(4,5)  =  10.45;
      heat(5,0)  = 0.30;  heat(5,1)  =   14.05;  heat(5,2)  =   4.44;  heat(5,3)  = ZERO;  heat(5,4)  =  3.22;  heat(5,5)  =   9.95;
      heat(6,0)  = 0.40;  heat(6,1)  =   13.08;  heat(6,2)  =   4.10;  heat(6,3)  = ZERO;  heat(6,4)  =  3.38;  heat(6,5)  =  10.55;
      heat(7,0)  = 0.50;  heat(7,1)  =   11.55;  heat(7,2)  =   3.56;  heat(7,3)  = ZERO;  heat(7,4)  =  3.65;  heat(7,5)  =  11.39;
      heat(8,0)  = 0.60;  heat(8,1)  =   11.03;  heat(8,2)  =   3.48;  heat(8,3)  = ZERO;  heat(8,4)  =  4.55;  heat(8,5)  =  12.68;
      heat(9,0)  = 0.70;  heat(9,1)  =   13.91;  heat(9,2)  =   4.47;  heat(9,3)  = ZERO;  heat(9,4)  =  3.29;  heat(9,5)  =   9.99;
      heat(10,0) = 0.80;  heat(10,1) =   12.12;  heat(10,2) =   3.59;  heat(10,3) = ZERO;  heat(10,4) =  3.68;  heat(10,5) =  11.18;
      heat(11,0) = 0.90;  heat(11,1) =   11.31;  heat(11,2) =   3.35;  heat(11,3) = ZERO;  heat(11,4) =  4.48;  heat(11,5) =  13.24;
      heat(12,0) = 1.00;  heat(12,1) =   17.46;  heat(12,2) =   7.08;  heat(12,3) = ZERO;  heat(12,4) = 15.13;  heat(12,5) =  32.25;

      
      /* battery open cell voltage vs. soc */
      b->ocv[0][0]  = 0.00;  b->ocv[0][1]  = 2.749;
      b->ocv[1][0]  = 0.01;  b->ocv[1][1]  = 2.833;
      b->ocv[2][0]  = 0.02;  b->ocv[2][1]  = 2.917;
      b->ocv[3][0]  = 0.03;  b->ocv[3][1]  = 3.001;
      b->ocv[4][0]  = 0.04;  b->ocv[4][1]  = 3.085;
      b->ocv[5][0]  = 0.05;  b->ocv[5][1]  = 3.169; 
      b->ocv[6][0]  = 0.10;  b->ocv[6][1]  = 3.212;
      b->ocv[7][0]  = 0.15;  b->ocv[7][1]  = 3.233;
      b->ocv[8][0]  = 0.20;  b->ocv[8][1]  = 3.259;
      b->ocv[9][0]  = 0.25;  b->ocv[9][1]  = 3.277;
      b->ocv[10][0] = 0.30;  b->ocv[10][1] = 3.290;
      b->ocv[11][0] = 0.35;  b->ocv[11][1] = 3.295;
      b->ocv[12][0] = 0.40;  b->ocv[12][1] = 3.297;
      b->ocv[13][0] = 0.45;  b->ocv[13][1] = 3.298;
      b->ocv[14][0] = 0.50;  b->ocv[14][1] = 3.299;
      b->ocv[15][0] = 0.55;  b->ocv[15][1] = 3.300;
      b->ocv[16][0] = 0.60;  b->ocv[16][1] = 3.303;
      b->ocv[17][0] = 0.65;  b->ocv[17][1] = 3.332;
      b->ocv[18][0] = 0.70;  b->ocv[18][1] = 3.335;
      b->ocv[19][0] = 0.75;  b->ocv[19][1] = 3.335;
      b->ocv[20][0] = 0.80;  b->ocv[20][1] = 3.335;
      b->ocv[21][0] = 0.85;  b->ocv[21][1] = 3.336;
      b->ocv[22][0] = 0.90;  b->ocv[22][1] = 3.336;
      b->ocv[23][0] = 0.95;  b->ocv[23][1] = 3.337;
      b->ocv[24][0] = 0.96;  b->ocv[24][1] = 3.368;
      b->ocv[25][0] = 0.97;  b->ocv[25][1] = 3.399;
      b->ocv[26][0] = 0.98;  b->ocv[26][1] = 3.432;
      b->ocv[27][0] = 0.99;  b->ocv[27][1] = 3.463;
      b->ocv[28][0] = 1.00;  b->ocv[28][1] = 3.495;
   }

   /* catl 306*Ahrs, for Q2.0 */
   if(strcmp("catl_306Ahr",simmain->batteryModelName) == 0)
   {
      fprintf(LOGFILE," Using the CATL 306 A*hr battery properties\n\n");
                         /* SOC, charge heat (W), discharge heat (W)              */
                         /* this table is at 25 degrees C (Cell temp?)            */
                         /* soc   0.50DP    0.25DP     0        0.25CP  0.50CP    */
                         /*        -150A     -75A      0A         75A    150A     */
                        /* updated for Q2 CATL306 cells at BOL on October 10 2025 */
      heat(0,0)  = 0.00;  heat(0,1)  = -b->cellCapacityAh*0.50;  heat(0,2)  = -b->cellCapacityAh*0.25;  heat(0,3)  = ZERO;  heat(0,4)  = b->cellCapacityAh*0.25;  heat(0,5)  = b->cellCapacityAh*0.50;
      heat(1,0)  = 0.00;  heat(1,1)  =   17.17;  heat(1,2)  =   6.87;  heat(1,3)  = ZERO;  heat(1,4)  =  4.08;  heat(1,5)  =  11.46;
      heat(2,0)  = 0.10;  heat(2,1)  =   11.66;  heat(2,2)  =   4.63;  heat(2,3)  = ZERO;  heat(2,4)  =  3.65;  heat(2,5)  =   9.45;
      heat(3,0)  = 0.20;  heat(3,1)  =   11.66;  heat(3,2)  =   4.63;  heat(3,3)  = ZERO;  heat(3,4)  =  3.65;  heat(3,5)  =   9.45;
      heat(4,0)  = 0.30;  heat(4,1)  =   11.68;  heat(4,2)  =   4.61;  heat(4,3)  = ZERO;  heat(4,4)  =  3.83;  heat(4,5)  =   9.57;
      heat(5,0)  = 0.40;  heat(5,1)  =   10.81;  heat(5,2)  =   4.27;  heat(5,3)  = ZERO;  heat(5,4)  =  3.46;  heat(5,5)  =   8.90;
      heat(6,0)  = 0.50;  heat(6,1)  =    9.32;  heat(6,2)  =   3.69;  heat(6,3)  = ZERO;  heat(6,4)  =  3.61;  heat(6,5)  =   9.45;
      heat(7,0)  = 0.60;  heat(7,1)  =    9.55;  heat(7,2)  =   3.87;  heat(7,3)  = ZERO;  heat(7,4)  =  3.79;  heat(7,5)  =   9.89;
      heat(8,0)  = 0.70;  heat(8,1)  =   11.41;  heat(8,2)  =   4.42;  heat(8,3)  = ZERO;  heat(8,4)  =  3.41;  heat(8,5)  =   8.39;
      heat(9,0)  = 0.80;  heat(9,1)  =    9.83;  heat(9,2)  =   3.57;  heat(9,3)  = ZERO;  heat(9,4)  =  3.57;  heat(9,5)  =   9.34;
      heat(10,0) = 0.90;  heat(10,1) =    9.10;  heat(10,2) =   3.24;  heat(10,3) = ZERO;  heat(10,4) =  4.27;  heat(10,5) =  10.77;
      heat(11,0) = 1.00;  heat(11,1) =    9.02;  heat(11,2) =   3.23;  heat(11,3) = ZERO;  heat(11,4) =  5.54;  heat(11,5) =  14.17;


      /* CATL 306 A*hrs at 25 degrees C and 0.5C rate */
      b->ocv[0][0]  = 0.00;  b->ocv[0][1]  = 2.870;
      b->ocv[1][0]  = 0.01;  b->ocv[1][1]  = 2.970;
      b->ocv[2][0]  = 0.02;  b->ocv[2][1]  = 3.050;
      b->ocv[3][0]  = 0.03;  b->ocv[3][1]  = 3.120;
      b->ocv[4][0]  = 0.04;  b->ocv[4][1]  = 3.165;
      b->ocv[5][0]  = 0.05;  b->ocv[5][1]  = 3.195;
      b->ocv[6][0]  = 0.10;  b->ocv[6][1]  = 3.220;
      b->ocv[7][0]  = 0.15;  b->ocv[7][1]  = 3.245;
      b->ocv[8][0]  = 0.20;  b->ocv[8][1]  = 3.265;
      b->ocv[9][0]  = 0.25;  b->ocv[9][1]  = 3.285;
      b->ocv[10][0] = 0.30;  b->ocv[10][1] = 3.295;
      b->ocv[11][0] = 0.35;  b->ocv[11][1] = 3.295;
      b->ocv[12][0] = 0.40;  b->ocv[12][1] = 3.295;
      b->ocv[13][0] = 0.45;  b->ocv[13][1] = 3.300;
      b->ocv[14][0] = 0.50;  b->ocv[14][1] = 3.300;
      b->ocv[15][0] = 0.55;  b->ocv[15][1] = 3.305;
      b->ocv[16][0] = 0.60;  b->ocv[16][1] = 3.325;
      b->ocv[17][0] = 0.65;  b->ocv[17][1] = 3.335;
      b->ocv[18][0] = 0.70;  b->ocv[18][1] = 3.335;
      b->ocv[19][0] = 0.75;  b->ocv[19][1] = 3.335;
      b->ocv[20][0] = 0.80;  b->ocv[20][1] = 3.335;
      b->ocv[21][0] = 0.85;  b->ocv[21][1] = 3.335;
      b->ocv[22][0] = 0.90;  b->ocv[22][1] = 3.335;
      b->ocv[23][0] = 0.95;  b->ocv[23][1] = 3.335;
      b->ocv[24][0] = 0.96;  b->ocv[24][1] = 3.335;
      b->ocv[25][0] = 0.97;  b->ocv[25][1] = 3.340;
      b->ocv[26][0] = 0.98;  b->ocv[26][1] = 3.355;
      b->ocv[27][0] = 0.99;  b->ocv[27][1] = 3.380;
      b->ocv[28][0] = 1.00;  b->ocv[28][1] = 3.470;
   }
   else
   {
      fprintf(LOGFILE," The battery name called out is not recognized\n");
      fprintf(LOGFILE," Recognized battery names are:  eve_306Ahr\n");
      fprintf(LOGFILE,"                                catl_306Ahr\n");
      fprintf(LOGFILE," Exiting\n");
      exit(1);
   }


//   fprintf(LOGFILE," battery cell heat:


   return ;
}


void setupHvac(struct SimMain *simmain)
{
   if(strcmp("no",IS_THERE_AN_HVAC)  == 0)
   {
      simmain->hvacYesOrNo = NO;
      fprintf(LOGFILE," The 4kW HVAC will be present in this case\n");
   }
   else if(strcmp("yes",IS_THERE_AN_HVAC) == 0)
   {
      simmain->hvacYesOrNo = YES;
      fprintf(LOGFILE," The 4kW HVAC will not be present in this case\n");
   }
   else
   {
      fprintf(LOGFILE,"\n\n  No explicit callout for and HVAC was made in the input file");
      fprintf(LOGFILE,"\n  An HVAC will not be present in this simulation");
      fprintf(LOGFILE,"\n  You may call out that an HVAC is present on this configuration");
      fprintf(LOGFILE,"\n  Using @HVAC_PRESENT{ yes } or @HVAC_PRESENT{ no }");

      simmain->hvacYesOrNo = NO;
      return ;
   }

   return ;
}



