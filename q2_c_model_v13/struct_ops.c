

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "data_structures.h"
#include "preprocess.h"

struct Battery        *initializeBattery(struct SimMain *simmain);
struct Inverter       *initializeInverter(struct SimMain *simmain);
struct Chiller        *initializeChiller(struct SimMain *simmain);
struct Hvac           *initializeHvac(struct SimMain *simmain);
struct Dehumidifier   *initializeDehumidifier(struct SimMain *simmain);
struct AuxLoad        *initializeAuxLoad(struct SimMain *simmain,double electricalPowerDraw);
struct TimeHistory    *initializeTimeHistoryElement(struct SimMain *simmain);
struct CoolantStream  *initializeStream(double volumeFlowRateLPM,double volumeLiters,double refFlowRate,double coldUA,double hotUA);
struct TimeHistory    *addToCurrentProfile(struct SimMain *simmain);
struct TimeHistory    *addToPowerProfile(struct SimMain *simmain);
struct ThermalWall    *initializeThermalWall(struct SimMain *simmain,double pcntTotalArea,double thickness,double density,double conductivity,double cp);

void                  readPowerProfileAndConvertItToCurrentProfile(struct SimMain *simmain);


void initialize(struct SimMain *simmain)
{
   simmain->tMax                   = 24.0*CONVERT_HOURS_TO_SECONDS;
   simmain->dt                     = 00.25;

   /* system electrical power during charge/discharge, in Watts */
   simmain->maxSystemPower         = NO_INPUT;
   simmain->currentSystemPower     = ZERO;
   simmain->peakAuxPower           = -999999.0;

   simmain->cRate                  = NO_INPUT;
   simmain->dRate                  = NO_INPUT;

   simmain->initialTemperature     = NO_INPUT;
   simmain->ambientTemperature     = NO_INPUT;
   simmain->radiationModelOnOrOff  = ON;       /* gets turned off if there is no sunrise or sunset time called out */
   simmain->radiationLoad          = ZERO;
   simmain->sunriseTime            = NO_INPUT;
   simmain->sunsetTime             = NO_INPUT;
   simmain->ambientTempSum         = ZERO;                  /* used to calculate average ambient temp      */
                                                            /* calculate the average ambient temp, useful  */
                                                            /* in cases where it changes in time           */
   simmain->containerWallPcntSteel = 0.15;
   simmain->containerWallArea      = 63.78;                 /* m2 of outer surface area                     */
                                                            /* Q1.0 -> 37.39 m^2                            */
                                                            /* Q2.0 -> 63.78 m^2                            */
                                                            /* Q3.0 -> 71.91 m^2                            */
   simmain->radiationSurfaceArea   = 0.4*63.78;

   simmain->circRunTimer           = ZERO;
   simmain->cameFromStandby        = NO;

   simmain->hvacYesOrNo            = NO_INPUT;

   simmain->bol_eol                = NO_INPUT;

   /* set the container inputs */
   simmain->containerWallUA        = 103.0;                 /* W/K, from some CFD analysis -> not used now */
   simmain->internalAirTemp        = NO_INPUT;
   simmain->internalAirTempPrev    = NO_INPUT;
   simmain->totalAuxEnergy         = ZERO;
   simmain->currentFileTag         = NULL;
   simmain->tempFileTag            = NULL;

   simmain->simIteration           = 0;
   simmain->resultOutputFrequency  = 60;

   simmain->chillerMode            = CIRCULATE_MODE;

   simmain->cycle                  = NULL;

   simmain->c                      = NULL;
   simmain->b                      = NULL;
   simmain->i                      = NULL;
   simmain->h                      = NULL;
   simmain->d                      = NULL;
   simmain->a                      = NULL;

   simmain->th                     = NULL;

   /* this is a place to load up the current profile              */
   /* if it's left null, then the hard-coded profile will be used */
   simmain->cProfile               = NULL;

   /* this is where a temperature profile can be read from a file */
   /* if it's left null, then the hard-coded profile will be used */
   simmain->tProfile               = NULL;


   /* initialize and set battery inputs */
   batteryListHead = initializeBattery(simmain);

   /* initialize and set inverter/pcs inputs */
//   inverterListHead = initializeInverter(simmain);

   /* initialize and set chiller inputs  -  put this after battery and inverter initialization because */
   /*                                       it needs to know if there is a battery or inverter         */
   chillerListHead = initializeChiller(simmain);

   /* initialize and set hvac inputs */
   hvacListHead = initializeHvac(simmain);

   /* initialize and set dehumidifier inputs */
   dehumidifierListHead = initializeDehumidifier(simmain);


   /* add other constant electrical loads */
   auxLoadListHead = initializeAuxLoad(simmain,300.0);  /* the ECC draws 50.0 W constantly */


   /* add discretized exterior walls in two parts      */
   /* steel, considered to be 15% of the area          */
   /* steel density is reduced to account for the fact that there is air in the beams */
   simmain->tw1 = initializeThermalWall(simmain,0.30,0.040,7833.0/4.0,50.0,465.0);

   /* and insulation, considered to be 85% of the area */
   simmain->tw2 = initializeThermalWall(simmain,0.70,0.040,150.0,0.045,700.0);


   simmain->totalAmbientHeatExchange   = ZERO;
   simmain->totalRadiationHeatExchange = ZERO;

   simmain->outFile                    = NULL;
   simmain->inFile                     = NULL;
   simmain->logFile                    = fopen("log.out","w");
   if(simmain->logFile == NULL){  printf("\n\n *** Error opening log.out.  Quitting ***\n\n"); exit(1); }

   fprintf(LOGFILE,"\n   *** Running Q2 Simulator ***\n\n");


   return ;
}


struct Chiller *initializeChiller(struct SimMain *simmain)
{
   struct Chiller *p;
   p                 = (struct Chiller *) malloc(sizeof(OChiller));
   int i;

   for(i=0;i<=11;i++)
   {
                        /* ambient temp */  /* cooling power @ 18C */       /* compressor power @ 18C */
      p->cooling18[i][0]   = NO_INPUT;   p->cooling18[i][1]  = NO_INPUT;    p->cooling18[i][2]  = NO_INPUT;
      p->cooling23[i][0]   = NO_INPUT;   p->cooling23[i][1]  = NO_INPUT;    p->cooling23[i][2]  = NO_INPUT;
   }

   p->pumpAuxCap             = ONE;
   p->compAuxCap             = ONE;
   p->coolingPowerCoeff      = ONE;


   /* cooling table for the refrigerated loop */
   /*                                         */
   /*              QUANTUM 3.0                */
   /*     0.25C  ENVICOOL CHILLER TABLES      */
   /*                                         */

   /*                                         */
   /*              QUANTUM HE                 */
   /*     10kW  ENVICOOL CHILLER TABLES       */
   /*                                         */
                        /* ambient temp */  /* cooling power @ 15C */       /* compressor power @ 15C */
/*   p->cooling15[0][0]   = (-30.0 + 273.15);   p->cooling15[0][1]  = 14000.0;    p->cooling15[0][2]  = 3200.0;
   p->cooling15[1][0]   = (-10.0 + 273.15);   p->cooling15[1][1]  = 13400.0;    p->cooling15[1][2]  = 3300.0;
   p->cooling15[2][0]   = ( 00.0 + 273.15);   p->cooling15[2][1]  = 12700.0;    p->cooling15[2][2]  = 3450.0;
   p->cooling15[3][0]   = ( 05.0 + 273.15);   p->cooling15[3][1]  = 12500.0;    p->cooling15[3][2]  = 3550.0;
   p->cooling15[4][0]   = ( 15.0 + 273.15);   p->cooling15[4][1]  = 12250.0;    p->cooling15[4][2]  = 3700.0;
   p->cooling15[5][0]   = ( 20.0 + 273.15);   p->cooling15[5][1]  = 11600.0;    p->cooling15[5][2]  = 3800.0;
   p->cooling15[6][0]   = ( 25.0 + 273.15);   p->cooling15[6][1]  = 11300.0;    p->cooling15[6][2]  = 3950.0;
   p->cooling15[7][0]   = ( 30.0 + 273.15);   p->cooling15[7][1]  = 10800.0;    p->cooling15[7][2]  = 4200.0;
   p->cooling15[8][0]   = ( 35.0 + 273.15);   p->cooling15[8][1]  = 10000.0;    p->cooling15[8][2]  = 4500.0;
   p->cooling15[9][0]   = ( 40.0 + 273.15);   p->cooling15[9][1]  = 9000.0;     p->cooling15[9][2]  = 4800.0;
   p->cooling15[10][0]  = ( 45.0 + 273.15);   p->cooling15[10][1] = 8500.0;     p->cooling15[10][2] = 5050.0;
   p->cooling15[11][0]  = ( 50.1 + 273.15);   p->cooling15[11][1] = 6200.0;     p->cooling15[11][2] = 4800.0;

   p->cooling20[0][0]   = (-30.0 + 273.15);   p->cooling20[0][1]  = 14000.0;    p->cooling20[0][2]  = 3200.0;
   p->cooling20[1][0]   = (-10.0 + 273.15);   p->cooling20[1][1]  = 13400.0;    p->cooling20[1][2]  = 3300.0;
   p->cooling20[2][0]   = ( 00.0 + 273.15);   p->cooling20[2][1]  = 12700.0;    p->cooling20[2][2]  = 3450.0;
   p->cooling20[3][0]   = ( 05.0 + 273.15);   p->cooling20[3][1]  = 12500.0;    p->cooling20[3][2]  = 3550.0;
   p->cooling20[4][0]   = ( 15.0 + 273.15);   p->cooling20[4][1]  = 12250.0;    p->cooling20[4][2]  = 3700.0;
   p->cooling20[5][0]   = ( 20.0 + 273.15);   p->cooling20[5][1]  = 11600.0;    p->cooling20[5][2]  = 3800.0;
   p->cooling20[6][0]   = ( 25.0 + 273.15);   p->cooling20[6][1]  = 11300.0;    p->cooling20[6][2]  = 3950.0;
   p->cooling20[7][0]   = ( 30.0 + 273.15);   p->cooling20[7][1]  = 10800.0;    p->cooling20[7][2]  = 4200.0;
   p->cooling20[8][0]   = ( 35.0 + 273.15);   p->cooling20[8][1]  = 10000.0;    p->cooling20[8][2]  = 4500.0;
   p->cooling20[9][0]   = ( 40.0 + 273.15);   p->cooling20[9][1]  = 9000.0;     p->cooling20[9][2]  = 4800.0;
   p->cooling20[10][0]  = ( 45.0 + 273.15);   p->cooling20[10][1] = 8500.0;     p->cooling20[10][2] = 5050.0;
   p->cooling20[11][0]  = ( 50.1 + 273.15);   p->cooling20[11][1] = 6200.0;     p->cooling20[11][2] = 4800.0;
*/

   p->batteryColdSideTemp = simmain->initialTemperature ; //INITIAL_TEMPERATURE;    /* initial value   */
//   p->battHxThermalMass   = 2.0*910.0;        /* 2kg of aluminum */
   p->compressorPcnt      = ZERO;
   p->batteryDemand       = ZERO;
   p->batterySensitivity  = 3.0;
   p->pcsDemand           = ZERO;
   p->inverterSensitivity = 30.0;
   p->sharingEnthalpy     = ZERO;

   p->circulationTimer    = ZERO;
   p->pumpOffTimer        = ZERO;

   p->timeSpentOperating       = ZERO;
   p->timeSpentResting         = ZERO;
   p->timeSpentIdling          = ZERO;


   /* track power and cumulative energy */
   p->currentAuxPower     = ZERO;

   p->bTurnedOn           = NO;
   p->batteryPumpPcnt     = ZERO;
   p->batteryPumpOnOff    = OFF;
   p->bPumpWasLastOn      = ZERO;

   p->pTurnedOn           = NO;
   p->inverterPumpPcnt    = ZERO;
   p->inverterPumpOnOff   = OFF;
   p->pPumpWasLastOn      = ZERO;

   p->fanPcnt             = ZERO;
   p->fansOnOff           = OFF;

   p->heaterPcnt          = ZERO;

   p->cumulativeAuxEnergy = ZERO;
   p->totalAuxEnergy      = ZERO;
   p->operatingAuxEnergy  = ZERO;
   p->restingAuxEnergy    = ZERO;
   p->idlingAuxEnergy     = ZERO;

   p->batteryTemperatureTarget    = 295.15;
   p->inverterTemperatureTarget   = 303.15;
   p->sharingTemperatureThreshold = simmain->ambientTemperature + 3.0;


   /* these power values are multiplied by percent, from 0 to 1, to get power of each component in the code */
   p->compressorOnOff           = OFF;
//   p->fanAuxPowerPerPcnt        = 7639.0;                  /* max fan power from the Bergstrom estimate, 2000.0 RPM is 100%  */
//   p->batPumpPowerPerPcnt       = 3835.0;                  /* max battery pump power, 1500.0 RPM is 100%                     */
//   p->pcsPumpPowerPerPcnt       = 1450.0;                  /* max pcs pump power, 1500.0 RPM is 100%                         */
//   p->fanAuxPowerPerPcnt        = 3300.0;                  /* max fan power from Envicool          October 1 2025              */
//   p->batPumpPowerPerPcnt       = 4100.0;                  /* max battery pump power from Envicool October 1 2025              */
   p->fanAuxPowerPerPcnt        = ZERO;                  /* max fan power from Envicool          October 1 2025              */
   p->batPumpPowerPerPcnt       = ZERO;                  /* max battery pump power from Envicool October 1 2025              */
   p->pcsPumpPowerPerPcnt       = ZERO;                  /* max pcs pump power     from Envicool October 1 2025              */
   p->electronicsAuxPower       = 200.0;

//   p->batVolumeFlowRatePerPcnt  = 480.0/60000.0;           /* internal units are always m3/s */
   p->batVolumeFlowRatePerPcnt  = 400.0/60000.0;           /* internal units are always m3/s */
   p->pcsVolumeFlowRatePerPcnt  = 120.0/60000.0;           /* internal units are always m3/s */

   p->batteryStream       = initializeStream(5.0,400.0,480.0,25000.0/7.0,20000.0/30.0);   /* the hotUA is a dummy value here */
   if(simmain->i != NULL)  p->inverterStream      = initializeStream(5.0,100.0,120.0,300.0,200.0/15.0);


   p->imTurnedOn          = NO;

   NEXT(p)                = NULL;


   return p;
}


struct Battery *initializeBattery(struct SimMain *simmain)
{
   int i;
   struct Battery *p;
   p              = (struct Battery *) malloc(sizeof(OBattery));

   p->mass        = 80.0*320.0;         /* kg, mass of all batteries in Q3.0 */
   p->cp          = 990.0;
   p->k           = 9.0;
   p->area        = 80.0*1.0;          /* cold plate area is 1.32 m2 and there are 48 of them */
   p->thermalMass = p->mass * p->cp;
   p->height      = 0.204;              /* height of battery in m */
   p->dx          = p->height / 7.0;


   p->batteryTemperatureTarget = 20.0 + 273.15;
   p->hysteresis               = 1.0;

   p->maxBatteryTemp           = ZERO;
   p->battAveTempOperating     = ZERO;
   p->battAveTempNotOperating  = ZERO;

//   p->coolantTemp              = 273.15 + 18.0;
   p->bottomUA                 = 100.0;              /* had this at 32 W/m2 K before, very low */
   p->topUA                    = 15.0;

   p->heatIntoColdPlate        = ZERO;
   p->hicpLast                 = ZERO;
   p->heatIntoAir              = ZERO;
   p->cumulativeBatteryHeat    = ZERO;
//   p->totalBatteryEnergy       = 1331.2*314.0*12.0;  /* 1331.2 Volts * 314.0 A*hrs * 12 strings per container */
   p->totalBatteryEnergy       = (3.47*52.0)*(304.0*80.0);
   p->initialSoh               = ONE;
   p->soh                      = p->initialSoh;
   p->soc                      = 0.01;               /* initial SOC */
   //p->soc                      = 1.00;               /* initial SOC */
   p->current                  = ZERO;

   for(i=0;i<7;i++){  p->temperature[i] = NO_INPUT; /*INITIAL_TEMPERATURE;*/
                      p->tempLast[i]    = NO_INPUT; /*INITIAL_TEMPERATURE;*/ }

   p->aveTempWhileResting      = ZERO;
   p->aveTempWhileCorD         = ZERO;


   NEXT(p)        = NULL;

   return p;
}

/*
struct Inverter *initializeInverter(struct SimMain *simmain)
{
   struct Inverter *p;
   p = (struct Inverter *) malloc(sizeof(OInverter));

   p->uaToAir                = 40.0;

   p->temperature            = 293.15;
   p->tempLast               = 293.15;
   p->pcsMass                = 75.0*3.0;
   p->pcsCp                  = 1500.0;

   p->currentAuxPower        = ZERO;
   p->totalAuxEnergy         = ZERO;

   p->heatIntoColdPlate      = ZERO;
   p->inverterHeat           = ZERO;
   p->cumulativeInverterHeat = ZERO;

   NEXT(p)                   = NULL;

   return p;
}
*/



struct CoolantStream *initializeStream(double volumeFlowRateLPM,double volumeLiters,double refFlowRate,double chillerSideUA,double coldPlateSideUA)
{
   struct CoolantStream *p;
   p = (struct CoolantStream *) malloc(sizeof(OCoolantStream));

   p->volumeFlowRate      = volumeFlowRateLPM/60000.0;       /* convert to m3/s */ 
   p->massFlowRate        = p->volumeFlowRate*1050.0;
   p->coolantVolume       = volumeLiters/1000.0;             /* convert to m3   */
   p->coolantCp           = 3400.0;                          /* J/kg K          */

   /* UA's are functions of flow rate */
   /* this is physically correct and keeps the system stable as well */
//   p->chillerUA           = coldUA*refFlowRate*1050.0/60000.0;
//   p->coldPlateUA         = hotUA*refFlowRate*1050.0/60000.0;           /* UA for the dry cooler loop */

   p->chillerUA           = chillerSideUA;
   p->coldPlateUA         = coldPlateSideUA;                 /* UA for the dry cooler loop */

   p->tempEnteringChiller = 273.15 + 20.0;
   p->tempLeavingChiller  = 273.15 + 20.0;

   p->tlcLast             = 273.15 + 20.0;
   p->tecLast             = 273.15 + 20.0;

   NEXT(p)                = NULL;

   return p;
}




struct Hvac *initializeHvac(struct SimMain *simmain)
{
   struct Hvac *p;
   p = (struct Hvac *) malloc(sizeof(OHvac));

   p->airTemp           = simmain->initialTemperature;
   p->UA                = 2.0;
   p->temperatureTarget = 273.15 + 40.0;
   p->hysteresis        = 20.0;
   p->currentAuxPower   = ZERO;
   p->coolingPower      = ZERO;

   p->totalAuxEnergy    = ZERO;

   NEXT(p)              = NULL;

   return p;
}


struct Dehumidifier *initializeDehumidifier(struct SimMain *simmain)
{
   struct Dehumidifier *p;
   p = (struct Dehumidifier *) malloc(sizeof(ODehumidifier));

   p->currentAuxPower              = ZERO;
   p->totalAuxEnergy               = ZERO;
   p->cumulativeDehumidifierOnTime = ZERO;

   NEXT(p)                         = NULL;

   return p;
}



struct AuxLoad *initializeAuxLoad(struct SimMain *simmain,double electricalPowerDraw)
{
   struct AuxLoad *p;
   p = (struct AuxLoad *) malloc(sizeof(OAuxLoad));

   p->currentAuxPower = electricalPowerDraw;

   NEXT(p) = NULL;

   return p;
}



double tableInterpolateCooling(double temp,double table[][3])
{
   double value;
   int i,n=0;


   if(temp < table[0][0])
   {
      return table[0][1] + ((table[1][1] - table[0][1])/(table[1][0] - table[0][0]))*(temp-table[0][0]);
   }

   for(i=0;i<=11;i++)
   {
      if((temp >= table[i][0]) && (temp <= table[i+1][0])) { return table[n][1] + ( (table[n+1][1]-table[n][1]) / (table[n+1][0]-table[n][0]))*(temp-table[n][0]); }
      n++;
   }

   if(temp >= table[11][0])
   {
      return table[11][1] + ((table[11][1] - table[10][1])/(table[11][0] - table[10][0]))*(temp-table[11][0]);
   }


 
   return table[n-1][1] + ((table[n-1][1]-table[n-2][1]) / (table[n-1][0]-table[n-2][0]))*(temp-table[n-1][0]);
}



double tableInterpolateAux(double temp,double table[][3])
{
   double value;
   int i,n=0;


   if(temp < table[0][0])
   {
      return table[0][2] + ((table[1][2] - table[0][2])/(table[1][0] - table[0][0]))*(temp-table[0][0]);
   }

   for(i=0;i<=11;i++)
   {
      if((temp >= table[i][0]) && (temp <= table[i+1][0])) { return table[n][2] + ( (table[n+1][2]-table[n][2]) / (table[n+1][0]-table[n][0]))*(temp-table[n][0]); }
      n++;// why is this here? --->  if(n>8) break;
   }

   if(temp >= table[11][0])
   {
      return table[11][2] + ((table[11][2] - table[10][2])/(table[11][0] - table[10][0]))*(temp-table[11][0]);
   }


 
   return table[n-1][2] + ((table[n-1][2]-table[n-2][2]) / (table[n-1][0]-table[n-2][0]))*(temp-table[n-1][0]);
}



double getValue(FILE *f)
{
   char c,l[2],b[20];
   char readas[20];

   b[0] = '\0';

   while((c=getc(f)) != EOF)
   {
      if(c == '{')
      {
         c = ' ';
      }
//      else if((c == '}') || (c == ','))
      /* return a value if there is a space or a newline */
      //else if((c == '}') || (c == ',') || (c == ' ') || (c == '\n'))
      else if((c == '}') || (c == ',') || (c == '\n'))
      {
         return atof(b);
      }
      /* the original getValue has this, but it's not pertinent for the file I'm trying to read now */
      else if( !( (c == ' ') || (c == '\n') || (c == '\t')))
      {
         l[0] = c;  l[1] = '\0';  strcat(b,l);
      }
   }
   return 0;
}


double getValueSpaces(FILE *f)
{
   char c,l[2],b[20];
   char readas[20];

   b[0] = '\0';

   while((c=getc(f)) != EOF)
   {
      if(c == '{')
      {
         c = ' ';
      }
//      else if((c == '}') || (c == ','))
      /* return a value if there is a space or a newline */
      else if((c == '}') || (c == ',') || (c == ' ') || (c == '\n'))
//      else if((c == '}') || (c == ',') || (c == '\n'))
      {
         return atof(b);
      }
      /* the original getValue has this, but it's not pertinent for the file I'm trying to read now */
      else if( !( (c == ' ') || (c == '\n') || (c == '\t')))
      {
         l[0] = c;  l[1] = '\0';  strcat(b,l);
      }
   }
   return 0;
}



void getString(FILE *f,char *d)
{
   char a[100]; a[0] = '\0';
   char l[2],c;

   while((c = getc(f)) != EOF)
   {
      if(c == '{')
      {
         c = ' ';
      }
      else if((c == '}') || (c == ','))
      {
         strcpy(d,a);
         return ;
      }
      else if( !( (c == ' ') || (c == '\n') || (c == '\t')))
      {
         l[0] = c; l[1] = '\0'; strcat(a,l);
      }
   }
}



void readPowerProfileAndConvertItToCurrentProfile(struct SimMain *simmain)
{
   FILE               *fin;
   struct TimeHistory *thisElement;

   fin = fopen(simmain->powerFileName,"r");
   if( fin == NULL){ fprintf(LOGFILE,"  No input file for current was found,");
                     fprintf(LOGFILE," a hard-coded current profile will be used\n\n");  return ; }

   /* if a file name has been called out */
   if( fin != NULL){ fprintf(LOGFILE,"  The current profile will be taken from an input file\n");
                     fprintf(LOGFILE,"  The input is considered to be power in kW of a string\n");
                     fprintf(LOGFILE,"  And there are 10 strings in total in this sytem\n");       }

   while(getc(fin) != EOF)
   {
      fseek(fin,-1,SEEK_CUR);

      /* add a new element to the list of current vs time */
      thisElement = addToPowerProfile(simmain);

      /* read the time */
      thisElement->time  = getValueSpaces(fin);


      /* read the power, and divide by voltage to get current */
      /* in addition to adjusting by voltage, number of quantums, number of strings,    */
      /* I also need to apply a negative sign because the convention of the files I'm   */
      /* reading is opposite from what the code assumes                                 */
      /* there are also some efficiency gross-up factors at the end                     */
      //thisElement->value = -getValue(fin)*1000.0/(numberOfQuantums*12.0*1331.2 * (0.989*0.997*0.99*0.984*0.999));
      /* multiplied by 1000.0 because the input is in kW and we just want Watts */
      /* multiplied by 10.0 because the input is per string and there are 10 strings in the Quantum */
      /* made negative because of the convention between the input file and the code */
      thisElement->value = -getValueSpaces(fin)*1000.0*10.0;


      /* need to smooth this out because I was having issues with reading in negative 0 */
      if((thisElement->value < 0.001) && (thisElement->value >= -0.001)) thisElement->value = ZERO;
   }


   fclose(fin);

   /* set the last element used to the head of the list */
   simmain->powerFileTag =  powerProfileListHead;


   return ;
}



struct TimeHistory *initializeTimeHistoryElement(struct SimMain *simmain)
{
   struct TimeHistory *p;
   p                 = (struct TimeHistory *) malloc(sizeof(OTimeHistory));

   p->time  = NO_INPUT;
   p->value = NO_INPUT;

   NEXT(p) = NULL;

   return p;
}


struct TimeHistory *addToPowerProfile(struct SimMain *simmain)
{
   struct TimeHistory *t = powerProfileListHead;

   if(t == NULL)
   {
      powerProfileListHead = initializeTimeHistoryElement(simmain);
      return powerProfileListHead;
   }

   /* go to the end of the list */
   while(NEXT(t) != NULL)   t = NEXT(t);

   /* add an element at the end of the list */
   NEXT(t) = initializeTimeHistoryElement(simmain);

   return NEXT(t);
}



struct TimeHistory *addToCurrentProfile(struct SimMain *simmain)
{
   struct TimeHistory *t = currentProfileListHead;

   if(t == NULL)
   {
      currentProfileListHead = initializeTimeHistoryElement(simmain);
      return currentProfileListHead;
   }

   /* go to the end of the list */
   while(NEXT(t) != NULL)   t = NEXT(t);

   /* add an element at the end of the list */
   NEXT(t) = initializeTimeHistoryElement(simmain);

   return NEXT(t);
}


struct ThermalWall *initializeThermalWall(struct SimMain *simmain,double pcntTotalArea,double thickness,double density,double conductivity,double cp)
{
   struct ThermalWall *p;
   int i;

   /* go to the end of the ThermalWall List */

   p = (struct ThermalWall *) malloc(sizeof(OThermalWall));

   p->density        = density;
   p->area           = simmain->containerWallArea*pcntTotalArea;
   p->mass           = simmain->containerWallArea*pcntTotalArea*thickness*density;
   p->cp             = cp;
   p->conductivity   = conductivity;

   p->totalThickness = thickness;
   p->dx             = thickness/7.0;

   p->innerUA        = 8.0;
   p->outerUA        = 8.0;

   /* not currently using this */
   p->R[0] = ONE;
   p->R[1] = conductivity/(p->dx);
   p->R[2] = ONE;


   /* start the run with a linear temperature distribution across the wall thickness */
   for(i=0;i<7;i++)  p->temp[i]     = nextT_internal + ((simmain->ambientTemperature - nextT_internal)/7.0)*(i+1);
   for(i=0;i<7;i++)  p->tempLast[i] = nextT_internal + ((simmain->ambientTemperature - nextT_internal)/7.0)*(i+1);



   NEXT(p) = NULL;

   return p;
}


struct CDCycle *initializeCycle()
{
   struct CDCycle *p;

   p = (struct CDCycle *) malloc(sizeof(OCDCycle));

   /* user inputs */
   p->startTime  = NO_INPUT;
   p->targetSoc1 = NO_INPUT;
   p->waitTime   = NO_INPUT;
   p->targetSoc2 = NO_INPUT;

   /* calculated */
   p->endTime1   = NO_INPUT;
   p->startTime2 = NO_INPUT;
   p->endTime2   = NO_INPUT;

   p->power1     = NO_INPUT;
   p->power2     = NO_INPUT;

   NEXT(p) = NULL;

   return p;
}

