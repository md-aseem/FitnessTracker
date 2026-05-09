


#include <stdio.h>
#include <math.h>
#include "data_structures.h"
#include "preprocess.h"

void   readPowerProfileAndConvertItToCurrentProfile(struct SimMain *simmain);
void   radiationLoad(struct SimMain *simmain);

void   setOperatingPower(struct SimMain *simmain);
void   determineCurrent(struct SimMain *simmain);
void   setOperatingCurrent(struct SimMain *simmain);
void   setAmbientTemperature(struct SimMain *simmain);

void   updateBatteryTemperatures(struct SimMain *simmain,struct Battery *b);
//void   updatePcsTemperature(struct SimMain *simmain);
//doublerpcsHeatGeneration(struct SimMain *simmain);
void   updateControlState(struct SimMain *simmain);
void   coolingMode(struct SimMain *simmain);
void   heatingMode(struct SimMain *simmain);
void   circulateMode(struct SimMain *simmain);
void   standbyMode(struct SimMain *simmain);
int    setPumpCirculation(struct SimMain *simmain);

//double cellHeatGeneration(double current,double soc,double temp);   /* based on cell resistance, only ohmic heat */
double batteryTotalHeatGeneration(struct SimMain *simmain); //double current, double soc, double temp);
void   calculateAmbientHeatLoadAndInternalAirTemp(struct SimMain *simmain);
void   updateChillerConditionAndCool(struct SimMain *simmain);
void   updateHvacConditionAndCool(struct SimMain *simmain);
void   updateDehumidifierConditionAndDryOut(struct SimMain *simmain);
double tableInterpolateCooling(double temp,double table[][3]);
double tableInterpolateAux(double temp,double table[][3]);
void   updateStateOfCharge(struct SimMain *simmain);
void   updateStateOfHealth(struct SimMain *simmain);
double cellOCV(struct SimMain *simmain);
void   tabulateAuxEnergy(struct SimMain *simmain);
double compressorAuxPower(struct SimMain *simmain);
void   copyCurrentTimeValuesToPreviousTimeValues(struct SimMain *simmain);
void   standbyOrCirculate(struct SimMain *simmain);
double addToAverageBatteryTemperature(struct SimMain *simmain);
double radiationSurfaceHeatGain(struct SimMain *simmain);

void   setRefrigeratedLoopColdHXTemperature(struct SimMain *simmain);
void   setRefrigeratedLoopPumpSpeed(struct Chiller *c);
//void   setPCSPumpSpeed(struct Chiller *c);

void   writeOutputFileHeader(struct SimMain *simmain);
void   outputTimeStepResults(struct SimMain *simmain);
void   writeFinalOutputToScreen(struct SimMain *simmain);



void transientSolver(struct SimMain *simmain)
{
   struct Battery      *b;
   struct Chiller      *c;
   struct Hvac         *h;
   struct Dehumidifier *d;


   /* create the output files for the transient simulation */
   OUTPUTFILE = fopen("transient.out","w");     writeOutputFileHeader(simmain);


   /* get the power profile, if it exists, and convert power to current */
   readPowerProfileAndConvertItToCurrentProfile(simmain);


   /* get the ambient temperature profile, if it exists */


   fprintf(LOGFILE,"\n  *** RUNNING *** \n\n");


   while(simTime < simulationMaxDuration)
   {
      setOperatingPower(simmain);
      determineCurrent(simmain);
//      setOperatingCurrent(simmain);
      setAmbientTemperature(simmain);


      calculateAmbientHeatLoadAndInternalAirTemp(simmain);


      updateControlState(simmain);
      updateChillerConditionAndCool(simmain);               /* updates temperature of coolant leaving chiller                       */
      updateHvacConditionAndCool(simmain);
      updateDehumidifierConditionAndDryOut(simmain);        /* we're currently not tracking moisture and just running 2 hours a day */
      updateBatteryTemperatures(simmain,batteryListHead);   /* update battery temperatures and temp of coolant entering chiller     */


      /* update miscellaneous parameters */
      tabulateAuxEnergy(simmain);
      updateStateOfCharge(simmain);
      updateStateOfHealth(simmain);


      /* store values calculated in this time step as previous values */
      copyCurrentTimeValuesToPreviousTimeValues(simmain);


      /* write output file */
      if(Iteration%reportingIt == 0) outputTimeStepResults(simmain); 

      simTime += transientDt;   Iteration += 1;
   }

   /* report some important values */
   writeFinalOutputToScreen(simmain);

   fclose(OUTPUTFILE);

   return ;
}


void setOperatingPower(struct SimMain *simmain)
{
   struct CDCycle     *cyc = cycleListHead;
   struct TimeHistory *th  = simmain->powerFileTag;
   currentPower            = ZERO;

 //  return ;

   /* add the feature to read the current profile from a file here */
   if(powerProfileListHead != NULL)
   {
      /* go along the list until you exceed the time of a list element*/
      while(NEXT(th) != NULL){ if((simTime >= th->time) && (simTime <= NEXT(th)->time)) break;  th = NEXT(th); }
      /* after the table has run out, just return the last current value */
      /* it's silly perhaps, but one way to do it                        */
      if(NEXT(th) == NULL){ currentPower = th->value; return ;}

      /* interpolate between the current and next list elements to get the current */
      currentPower = th->value + ((NEXT(th)->value - th->value)/(NEXT(th)->time - th->time))*(simTime - th->time);
      simmain->powerFileTag = th;


      return ;
   }


   while(cyc != NULL)
   {
      if((simTime >= cyc->startTime)  && (simTime <= cyc->endTime1)) currentPower = cyc->power1;
      if((simTime >= cyc->startTime2) && (simTime <= cyc->endTime2)) currentPower = cyc->power2;

      cyc = NEXT(cyc);
   }



   /* if nothing else, a hard-coded profile */
//   currentPower = ZERO;  //return ;

/* one of the validation cycles for Q2.0 */
//   if((simTime >=  9.85*CONVERT_HOURS_TO_SECONDS) && (simTime <= 12.00*CONVERT_HOURS_TO_SECONDS))  currentPower =  maxDischargePower;
//   if((simTime >= 13.00*CONVERT_HOURS_TO_SECONDS) && (simTime <= 14.73*CONVERT_HOURS_TO_SECONDS))  currentPower =  maxChargePower;

/* one of the validation cycles for Q2.0 */
//   if((simTime >=  6.75*CONVERT_HOURS_TO_SECONDS) && (simTime <=  7.00*CONVERT_HOURS_TO_SECONDS))  currentPower =  maxChargePower;

//   if((simTime >=  9.85*CONVERT_HOURS_TO_SECONDS) && (simTime <= 12.00*CONVERT_HOURS_TO_SECONDS))  currentPower =  maxDischargePower;
//   if((simTime >= 13.00*CONVERT_HOURS_TO_SECONDS) && (simTime <= 15.15*CONVERT_HOURS_TO_SECONDS))  currentPower =  maxChargePower;

/* one of the validation cycles for Q2.0 */
//   if((simTime >=  4.85*CONVERT_HOURS_TO_SECONDS) && (simTime <=  7.00*CONVERT_HOURS_TO_SECONDS))  currentPower = maxDischargePower;
//   if((simTime >=  8.00*CONVERT_HOURS_TO_SECONDS) && (simTime <= 9.73*CONVERT_HOURS_TO_SECONDS))  currentPower =  maxChargePower;

//   if((simTime >= 11.73*CONVERT_HOURS_TO_SECONDS) && (simTime <= 13.46*CONVERT_HOURS_TO_SECONDS))  currentPower = maxDischargePower;
//   if((simTime >= 14.46*CONVERT_HOURS_TO_SECONDS) && (simTime <= 16.61*CONVERT_HOURS_TO_SECONDS))  currentPower = maxChargePower;

/* another validation cycle for Q2.0 */
//   if((simTime >=  7.70*CONVERT_HOURS_TO_SECONDS) && (simTime <= 12.00*CONVERT_HOURS_TO_SECONDS))  currentPower = maxDischargePower;
//   if((simTime >= 13.00*CONVERT_HOURS_TO_SECONDS) && (simTime <= 17.30*CONVERT_HOURS_TO_SECONDS))  currentPower = maxChargePower;

   return ; 
}


void determineCurrent(struct SimMain *simmain)
{
   currentCurrent = currentPower / (80.0*52.0*cellOCV(simmain));

   return ;
}



void setOperatingCurrent(struct SimMain *simmain)
{
   struct TimeHistory *th = simmain->currentFileTag;
   currentCurrent = ZERO; 

//   return ;

   /* if there is a current profile from a file, use it */
   /* this ends up taking a long time because it starts at 0 every time, it could be better */
   if(currentProfileListHead != NULL)
   {
      /* go along the list until you exceed the time of a list element*/
      while(NEXT(th) != NULL){ if((simTime >= th->time) && (simTime <= NEXT(th)->time)) break;  th = NEXT(th); }

      /* after the table has run out, just return the last current value */
      /* it's silly perhaps, but one way to do it                        */
      if(NEXT(th) == NULL){ currentCurrent = th->value; return ;}

      /* interpolate between the current and next list elements to get the current */
      currentCurrent = th->value + ((NEXT(th)->value - th->value)/(NEXT(th)->time - th->time))*(simTime - th->time);
      simmain->currentFileTag = th;

      return ;
   }


   /* if there is no time profile read in from a file, do the hard-coded thing below: */
   /* this is the cycle that is run at RCT on October 8 2025 */
//   if((simTime >= 11.00*CONVERT_HOURS_TO_SECONDS) && (simTime <= 14.66*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -90.0;
//   if((simTime >= 17.15*CONVERT_HOURS_TO_SECONDS) && (simTime <= 21.00*CONVERT_HOURS_TO_SECONDS))  currentCurrent =  90.0;

//   if((simTime >= 8.25*CONVERT_HOURS_TO_SECONDS) && (simTime <= 11.75*CONVERT_HOURS_TO_SECONDS))  currentCurrent =  75.0;
//   if((simTime >= 14.25*CONVERT_HOURS_TO_SECONDS) && (simTime <= 17.75*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -75.0;

   if((simTime >=  7.95*CONVERT_HOURS_TO_SECONDS) && (simTime <= 12.00*CONVERT_HOURS_TO_SECONDS))  currentCurrent =  150.0;
   if((simTime >= 13.00*CONVERT_HOURS_TO_SECONDS) && (simTime <= 17.05*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -150.0;

/**************************************************************************************/
/*                                                                                    */
/* test case for evaluating SOH preduction with 0.125C                                */
/*                                                                                    */
/**************************************************************************************/
//   if((simTime >= 2.05*CONVERT_HOURS_TO_SECONDS) && (simTime <=  5.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent =   37.5;
//   if((simTime >= 7.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 10.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -37.5;

//   if((simTime >=  2.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 9.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent =   37.5;
//   if((simTime >= 11.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 17.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -37.5;

//   if((simTime >=  2.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 9.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent =   37.5;
//   if((simTime >= 11.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 17.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -37.5;

/**************************************************************************************/
/*                                                                                    */
/* test case for evaluating SOH preduction with 0.250C                                */
/*                                                                                    */
/**************************************************************************************/
//   if((simTime >= 2.05*CONVERT_HOURS_TO_SECONDS)  && (simTime <= 5.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent =  75.0;
//   if((simTime >= 7.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 10.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -75.0;

//   if((simTime >= 12.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 15.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent =  75.0;
//   if((simTime >= 17.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 20.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -75.0;

/**************************************************************************************/
/*                                                                                    */
/* test case for evaluating SOH preduction with 0.333C                                */
/*                                                                                    */
/**************************************************************************************/
//   if((simTime >= 2.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 4.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent =  100.0;
//   if((simTime >= 6.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 8.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -100.0;

//   if((simTime >= 10.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 12.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent =  100.0;
//   if((simTime >= 14.05*CONVERT_HOURS_TO_SECONDS) && (simTime <= 16.95*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -100.0;

//   if((simTime >= 10.25*CONVERT_HOURS_TO_SECONDS) && (simTime <= 12.00*CONVERT_HOURS_TO_SECONDS))  currentCurrent =  150.0;
//   if((simTime >= 12.50*CONVERT_HOURS_TO_SECONDS) && (simTime <= 14.25*CONVERT_HOURS_TO_SECONDS))  currentCurrent = -150.0;

   return ;
}


void setAmbientTemperature(struct SimMain *simmain)
{
   struct TimeHistory *th = simmain->tempFileTag;

   return ; /* have this here to keep the input file number */

   /* if ambient temperature is constant */
//   simmain->ambientTemperature = AMBIENT_TEMPERATURE;   return ;

   if(tempProfileListHead != NULL)
   {
      while(NEXT(th) != NULL){ if((simTime >= th->time) && (simTime <= NEXT(th)->time)) break; th = NEXT(th); }

      if(NEXT(th) == NULL){ ambientT = th->value; return ;}

      ambientT = th->value + ((NEXT(th)->value - th->value)/(NEXT(th)->time - th->time))*(simTime - th->time);
      simmain->tempFileTag = th;

      return ;
   }


   /* if there is no time profile read in from a file, do the hard-coded thing below: */
   if((simTime >= 10.25*CONVERT_HOURS_TO_SECONDS) && (simTime <= 13.75*CONVERT_HOURS_TO_SECONDS))  ambientT = 273.15 + 30.0;

   if((simTime >= 14.75*CONVERT_HOURS_TO_SECONDS) && (simTime <= 18.25*CONVERT_HOURS_TO_SECONDS))  ambientT = 273.15 + 30.0;

   return ;
}




void calculateAmbientHeatLoadAndInternalAirTemp(struct SimMain *simmain)
{
   struct Inverter *p = inverterListHead;
   struct Battery  *b = batteryListHead;
   double radSurfaceTemp,resid,wallTemp;   resid = 0.10;  radSurfaceTemp = simmain->ambientTemperature + 2.0;
   double steelFluxToInnerAir, insulationFluxToInnerAir, pcsAirHeatExchange;
   int i;

   double fluxToInnerAir = ZERO;
   double steelFluxToInnerChunk, steelFluxToOuterChunk;
   double insulationFluxToInnerChunk, insulationFluxToOuterChunk;

   /* area is left out here, and this calculation is treated as being */
   /*  per meter^2.  Then the calculations are done and the areas are */
   /*  included later                                                 */
   double R[3] = {steelArea*(ONE/((ONE/wall1OuterUA) + ((wall1dx/TWO)/wall1K))),
                  steelArea*wall1K/wall1dx,
                  steelArea*(ONE/((ONE/wall1InnerUA) + ((wall1dx/TWO)/wall1K))) };

   double R2[3] = {insulationArea*(ONE/((ONE/wall2OuterUA) + ((wall2dx/TWO)/wall2K))),
                   insulationArea*wall2K/wall2dx,
                   insulationArea*(ONE/((ONE/wall2InnerUA) + ((wall2dx/TWO)/wall2K))) };


   /* calculate temperature and solar flux based on time of day       */
   /* 1.  Get solar load as a function of time (W/m2)                 */       
   /* 2.  Get % of surface exposed to radiation                       */
   /* 3.  Calculate temperature of this patch of surface based on     */
   /*     instantaneous equilibrium heat flux.  i.e. what temperature */
   /*     does the surface need to be in order to be in equilibrium   */
   /* 3a. Element [0] is the inner cold surface, Element [6] is the   */
   /*     outermost element that gets radiation heat                  */
   simmain->radiationIntensity     = 350.0;   /* 1000 W/m2 and absorptivity of 0.35 */
   simmain->pcntSurfaceInRadiation = ONE;

   /* radiation load will be calculated and directly added to the air         */ 
   /*   it will be a little involved to add it by heating up the external     */
   /*   surface and having a larger gradient, etc                             */
   /* the reason it will be involved is because I need to split up the        */
   /*   surface into two parts - one that gets radiation and one that doesn't */


   /* calculate the heat gain on the outer surface due to solar radiation */
   simmain->radiationLoad               = radiationSurfaceHeatGain(simmain);
   simmain->totalRadiationHeatExchange += simmain->radiationLoad*transientDt;

//   printf(" rad surface temp = ");
//   while(resid*resid > 0.001)
//   {
      /* the residual is the heat imbalance per unit area */
//      resid =   simmain->pcntSurfaceInRadiation*simmain->radiationIntensity         /* radiation flux into the surface         */
//              - wall2OuterUA*(radSurfaceTemp - simmain->ambientTemperature)         /* convection away from surface to ambient */
//              - 0.8*STEFAN_BOLTZMANN_CONSTANT*(TO_THE_FOURTH(radSurfaceTemp) - TO_THE_FOURTH(simmain->ambientTemperature)) /* radiation flux away */
//              - (radSurfaceTemp - wall2Tlast(6))*R[0];                              /* conduction into the wall */

//      radSurfaceTemp += 0.02*resid;
//      printf(" %f",radSurfaceTemp);
//   }
//   printf("\n");

   /* 4. Update steel discretized wall, tw1 */
   steelFluxToOuterChunk = simmain->radiationLoad + (simmain->ambientTemperature - wall1Tlast(6))*R[0] + (wall1Tlast(5) - wall1Tlast(6))*R[1];
/* works, without radiation: */
//   steelFluxToOuterChunk = (simmain->ambientTemperature - wall1Tlast(6))*R[0] + (wall1Tlast(5) - wall1Tlast(6))*R[1];
   steelFluxToInnerChunk = (prevT_internal - wall1Tlast(0))*R[2] + (wall1Tlast(1) - wall1Tlast(0))*R[1];
//   fluxToInnerAir        = -(prevT_internal - wall1Tlast(0))*R[2];
   fluxToInnerAir       -= (prevT_internal - wall1Tlast(0))*R[2];

   wall1T(0) = wall1Tlast(0) + steelFluxToInnerChunk*transientDt/(simmain->tw1->mass * simmain->tw1->cp / 7.0);
   wall1T(6) = wall1Tlast(6) + steelFluxToOuterChunk*transientDt/(simmain->tw1->mass * simmain->tw1->cp / 7.0);


   for(i=1;i<=5;i++)
   {
      wall1T(i) += ((wall1Tlast(i-1) - wall1Tlast(i))*R[1]
                +   (wall1Tlast(i+1) - wall1Tlast(i))*R[1])*transientDt/(simmain->tw1->mass * simmain->tw1->cp / 7.0);
   }



   /* 5. Update insulation discretized wall, tw2 */
   insulationFluxToOuterChunk = (simmain->ambientTemperature - wall2Tlast(6))*R2[0] + (wall2Tlast(5) - wall2Tlast(6))*R2[1];

   insulationFluxToInnerChunk = (prevT_internal - wall2Tlast(0))*R2[2] + (wall2Tlast(1) - wall2Tlast(0))*R2[1];
   fluxToInnerAir             += -(prevT_internal - wall2Tlast(0))*R2[2];

   wall2T(0) = wall2Tlast(0) + insulationFluxToInnerChunk*transientDt/(simmain->tw2->mass * simmain->tw2->cp / 7.0);
   wall2T(6) = wall2Tlast(6) + insulationFluxToOuterChunk*transientDt/(simmain->tw2->mass * simmain->tw2->cp / 7.0);
 
   for(i=1;i<=5;i++)
   {
      wall2T(i) += ((wall2Tlast(i-1) - wall2Tlast(i))*R2[1]
                +   (wall2Tlast(i+1) - wall2Tlast(i))*R2[1])*transientDt/(simmain->tw2->mass * simmain->tw2->cp / 7.0);
   }


   /* calculate heat flux into the inner air of the quantum */
//   pcsAirHeatExchange = p->uaToAir*(prevT_internal - p->tempLast);


   //nextT_internal                     = prevT_internal + (-pcsAirHeatExchange - b->heatIntoAir + fluxToInnerAir)*transientDt/(20.0*1006.0);
   nextT_internal                     = prevT_internal + (-b->heatIntoAir + fluxToInnerAir)*transientDt/(20.0*1006.0);
   simmain->totalAmbientHeatExchange += fluxToInnerAir*transientDt;

   simmain->ambientTempSum += simmain->ambientTemperature;

   return ;
}


double radiationSurfaceHeatGain(struct SimMain *simmain)
{
   double x,halfDuration,val;

   if(RADIATION_ON_OFF == OFF) return ZERO;

   if((simTime > simmain->sunriseTime) && (simTime < simmain->sunsetTime))
   {
      x            = simTime - (0.5*(simmain->sunriseTime + simmain->sunsetTime));
      halfDuration = 0.5*(simmain->sunsetTime - simmain->sunriseTime);

      /* calculate the amount of radiation */
      /* max heat influx = 1000 W/m2 at absorptivity of 0.35 -> 350.0 W/m2 */
      /* then it follows a pattern for the time of day                     */
//      val = simmain->radiationSurfaceArea*170.0*(ONE - (x*x/(halfDuration*halfDuration)));
      /* this produces a capped profile, consistent with lower intensity when the sun */
      /* is rising or setting but then fixed at a max value during the day            */
      val = 850.0*(ONE - (x*x/(halfDuration*halfDuration)));
      return simmain->radiationSurfaceArea*((val > 170.0) ? 170.0 : val);
   }

   /* if you don't go through the previous if statement, the sun isn't up, return zero */
   return ZERO;
}


void updateBatteryTemperatures(struct SimMain *simmain,struct Battery *b)
{
   struct Chiller  *c = chillerListHead;
//   struct Inverter *p = inverterListHead;
   int i;
   double bottomQ,topQ,maxEnthalpyDelta;

   double R[3] = {b->area*(ONE/((ONE/c->batteryStream->coldPlateUA) + ((b->dx/TWO)/b->k))),
                  b->area*b->k/b->dx,
                  b->area*(ONE/((ONE/b->topUA) + ((b->dx/TWO)/b->k))) };

   /* if there are no batteries in the list */
   if(b == NULL) return ;


   while(b != NULL)
   {
      /* calculate heat into the cold plate              */
      /* 1. Calculate max delta in enthalpy for the flow */
      /* 2.   */
      maxEnthalpyDelta = c->batteryStream->massFlowRate*c->batteryStream->coolantCp*(b->tempLast[0] - c->batteryStream->tlcLast);


      /* calculate heat flux at top and bottom elements */
//      bottomQ = (c->batteryStream->tlcLast - b->tempLast[0])*R[0] + (b->tempLast[1] - b->tempLast[0])*R[1];
      bottomQ = -0.4*maxEnthalpyDelta + (b->tempLast[1] - b->tempLast[0])*R[1];
      topQ    = (simmain->internalAirTemp - b->tempLast[6])*R[2] + (b->tempLast[5] - b->tempLast[6])*R[1];

      b->heatIntoAir       = (prevT_internal - b->tempLast[6])*R[2];
      b->heatIntoColdPlate = -0.4*maxEnthalpyDelta;


      /* give this heat to the battery coolant stream */
      c->batteryStream->tempEnteringChiller = c->batteryStream->tlcLast - b->heatIntoColdPlate/(c->batteryStream->massFlowRate*c->batteryStream->coolantCp);



      /* update temperatures of the top and bottom elements */
      b->temperature[0] += (bottomQ + (ONE/7.0)*batteryTotalHeatGeneration(simmain))*transientDt/(b->mass * b->cp / 7.0);
      b->temperature[6] += (topQ    + (ONE/7.0)*batteryTotalHeatGeneration(simmain) +  batteryTabHeat)*transientDt/(b->mass * b->cp / 7.0);


      /* update this to track and report total battery heat generated */
      b->cumulativeBatteryHeat += ((ONE/7.0)*batteryTotalHeatGeneration(simmain) +
                                   (ONE/7.0)*batteryTotalHeatGeneration(simmain) + batteryTabHeat)*transientDt;


      /* the middle elements of the battery */
      for(i=1;i<=5;i++)
      {
         b->temperature[i] += (((ONE/7.0)*batteryTotalHeatGeneration(simmain)) 
                           +  (b->tempLast[i-1] - b->tempLast[i])*R[1]
                           +  (b->tempLast[i+1] - b->tempLast[i])*R[1])*transientDt/(b->mass * b->cp / 7.0);

         b->cumulativeBatteryHeat += (ONE/7.0)*batteryTotalHeatGeneration(simmain)*transientDt;
      }

      /* calculate metrics for the SOH / fade model */
      if( CURRENT_IS_MOVING) b->aveTempWhileCorD    += addToAverageBatteryTemperature(simmain);
      else                   b->aveTempWhileResting += addToAverageBatteryTemperature(simmain);

      /* get a copy of the current time step temperatures for use during the next time step */
      for(i=0;i<=6;i++)  b->tempLast[i] = b->temperature[i];

      b = NEXT(b);
   }

   return ;
}

/*
void updatePcsTemperature(struct SimMain *simmain)
{
   struct Chiller *c  = chillerListHead;
   struct Inverter *p = inverterListHead;
   double maxEnthalpyDelta,airHeatExchange;

   airHeatExchange      = p->uaToAir*(prevT_internal - p->tempLast);
   maxEnthalpyDelta     = c->inverterStream->massFlowRate*c->inverterStream->coolantCp*(c->inverterStream->tlcLast - p->tempLast);
   p->heatIntoColdPlate = 0.6*maxEnthalpyDelta;
   p->temperature      += (airHeatExchange + pcsHeatGeneration(simmain) + 0.6*maxEnthalpyDelta)*transientDt/(p->pcsMass*p->pcsCp);



   c->inverterStream->tempEnteringChiller = c->inverterStream->tlcLast - 0.6*maxEnthalpyDelta/(c->inverterStream->massFlowRate*c->inverterStream->coolantCp);


   p->cumulativeInverterHeat += p->inverterHeat*transientDt;

   return ;
}
*/


double pcsHeatGeneration(struct SimMain *simmain)
{

   /* determine how much heat is generated by the PCS   */



   /* calculate how much of that is going to the air    */
   /*   it's based on 180W per PCS at full power        */


   /* the rest goes into the fluid                      */

   /* right now, let's hard-code in 6kW when the system */
   /* is running                                        */
   if(chargeOrDischargeIsHappening){  simmain->i->currentAuxPower = 100.0;   simmain->i->inverterHeat = 18000.0;   return 18000.0; }
   else{                              simmain->i->currentAuxPower = ZERO;    simmain->i->inverterHeat = ZERO;      return ZERO;    }
}



void updateControlState(struct SimMain *simmain)
{
   struct Battery  *b = batteryListHead;
   struct Chiller  *c = chillerListHead;
   struct Inverter *p = inverterListHead;


   /* This corresponds with circulate mode being trigged upon leaving */
   /* heating or cooling mode.  This function will count up until the */
   /* timer has run out */
   if(setPumpCirculation(simmain))  return ;


   /* check for cooling mode triggers */
   if((CHILLER_MODE == COOL_MODE                                   ) ||
/*    ( BATTERY_MIN_TEMP > BATTERY_COOL_TARGET                     ))   coolingMode(simmain); */
/* this part is for coolant temperature based control */
      (c->batteryStream->tlcLast > B_COOLANT_TARGET))  coolingMode(simmain);                                                                            


   /* check for heating mode triggers */
   if((CHILLER_MODE == HEAT_MODE                                   ) ||
//      (PCS_INLET        < PCS_MIN_TEMP                             ) ||
      (BATTERY_MAX_TEMP < BATTERY_HEAT_MIN                         ) ||
      (BATTERY_MIN_TEMP < BATTERY_HEAT_TARGET                      ))   heatingMode(simmain);


   /* check for circulation mode triggers */
   if(CHILLER_MODE == CIRCULATE_MODE )   circulateMode(simmain);


   /* check for stanby mode triggers */
   if(CHILLER_MODE == STANDBY_MODE )   standbyMode(simmain);


   return ;
}



void coolingMode(struct SimMain *simmain)
{
   struct Battery      *b = batteryListHead;
   struct Inverter     *p = inverterListHead;
   struct Chiller      *c = chillerListHead;
   double demand          = ZERO;   /* for use in control scheme 2 */
   double sensitivity     = 3.0;    /* for use in control scheme 2 */

   /* do some reporting about why you're entering cooling mode */
   if(CHILLER_MODE != COOL_MODE)
   {
      fprintf(LOGFILE,"\n %6.3f hours:  Entering Cooling Mode because ",simTime/3600.0);
/* battery temperature control */
//      if(BATTERY_MIN_TEMP > BATTERY_COOL_TARGET)
//         fprintf(LOGFILE,"BATTERY_MIN_TEMP > BATTERY_COOL_TARGET     -->  %7.3f > %7.3f\n",BATTERY_MIN_TEMP,BATTERY_COOL_TARGET);
/* coolant temperature control */
      if(c->batteryStream->tecLast > B_COOLANT_TARGET)
         fprintf(LOGFILE,"BATTERY_INLET_TEMP > B_COOLANT_TARGET      -->  %7.3f > %7.3f\n",c->batteryStream->tecLast,B_COOLANT_TARGET);
   }

   /* coming from standby mode?  from the algorithm diagram */
   if(CHILLER_MODE == STANDBY_MODE){  simmain->cameFromStandby = YES;   simmain->circRunTimer = ZERO; }

   /* set to chiller mode */
   CHILLER_MODE = COOL_MODE;


   /* check if the pumps should be on for circulation */
   /* if yes, then set them and leave cooling mode    */
   if(setPumpCirculation(simmain))  return ;

   /* set PCS target temperature */
   

   /* determine required PCS flow rate */



   /*                                                                  */
   /* *** CONTROL SCHEME 1:  THE MOST SIMPLE CONTROL SCHEME  ***       */
   /*                                                                  */
   /* if max battery temperature is above target + hysteresis, turn on */
/*   if(b->temperature[6] > (b->batteryTemperatureTarget + b->hysteresis)){   c->compressorPcnt = ONE;
                                                                              c->batteryDemand  = 0.80;
                                                                              c->inverterDemand = 0.80;
                                                                              c->fanPcnt        = 0.80;  } */

   /* if max battery temperature is below target, turn off */
/*   if(b->temperature[6] < b->batteryTemperatureTarget){                     c->compressorPcnt = ZERO;
                                                                              c->batteryDemand  = 0.80;
                                                                              c->inverterDemand = 0.80;
                                                                              c->fanPcnt        = 0.80;  } */

 
   /*                                                                  */
   /* *** CONTROL SCHEME 2:  ENVICOOL BASE CONTROL SCHEME ***          */
   /*                                                                  */
   //bDemand = (b->temperature[6] - c->batteryTemperatureTarget) /bSensitivity;
   bDemand = (b->temperature[6] - (BATTERY_COOL_MIN + ONE)) /bSensitivity;

   /* pcs demand is based on coolant temperature */
//   pDemand = (p->temperature    - (PCS_COOL_TARGET + ONE))/pSensitivity;


   /* set demand for the battery loop */
// if((bDemand >= 1.00) && (c->bTurnedOn == NO)) {c->compressorPcnt  = (bDemand > ONE) ? ONE : ((bDemand < 0.35) ? 0.35 : bDemand);
   if((bDemand >= 0.30) && (c->bTurnedOn == NO)) {c->compressorPcnt  = (bDemand > ONE) ? ONE : ((bDemand < 0.30) ? 0.30 : bDemand);
                                                   c->compressorPcnt  = c->compressorPcnt*c->coolingPowerCoeff;
                                                   c->compressorOnOff = ON;
                                                   c->batteryPumpPcnt = BATTERY_FLOW_0P25*c->pumpAuxCap;
                                                   c->bTurnedOn       = YES;
                                                   /*printf(" battery tripped on!\n");*/}

   if((bDemand >= 0.01) && (c->bTurnedOn == YES)){ c->compressorPcnt  = (bDemand > ONE) ? ONE : ((bDemand < 0.30) ? 0.30 : bDemand);
                                                   c->compressorPcnt  = c->compressorPcnt*c->coolingPowerCoeff;
                                                   c->compressorOnOff = ON;
                                                   c->batteryPumpPcnt = BATTERY_FLOW_0P25*c->pumpAuxCap;
                                                   /*printf(" maintain\n");*/}

   if((bDemand <  0.01) && (c->bTurnedOn == YES)){ c->compressorPcnt = ZERO;
                                                   c->compressorOnOff = OFF;
                                                   c->batteryPumpPcnt = 0.01;
                                                   c->bTurnedOn = NO;
                                                   /*printf(" tripped off!\n");*/}

/* determine pcs flow rate */
//   if(PCS_INLET < PCS_FLOW_TEMP){  c->inverterPumpPcnt = PCS_FLOW_LOW;   c->pTurnedOn = YES; }
//   else                         {  c->inverterPumpPcnt = PCS_FLOW_HIGH;  c->pTurnedOn = YES; }


   /* set fan conditions -> if battery of pcs cooling is operating, turn on */
   /*                       if everything is off, turn the fans off         */
   if(anyCoolingIsOn)   { c->fanPcnt = 0.80;  c->fansOnOff = ON;  }
   if(allCoolingIsOff)  { c->fanPcnt = ZERO;  c->fansOnOff = OFF; }

   /* can we leave cooling mode and go into standby mode? */
   if(/*(BATTERY_MAX_TEMP  < BATTERY_COOL_EXIT               ) ||*/
      (c->batteryStream->tecLast < (B_COOLANT_TARGET-3.0)    )                                                                            
      /*(BATTERY_MIN_TEMP  < BATTERY_COOL_MIN                )*/)   { fprintf(LOGFILE," %6.3f hours:  Leaving  Cooling Mode",simTime/3600.0);
//                                                                  if(BATTERY_MAX_TEMP < BATTERY_COOL_EXIT)                fprintf(LOGFILE," because BATTERY_MAX_TEMP < BATTERY_COOL_EXIT       -->  %7.3f < %7.3f\n                                     ",BATTERY_MAX_TEMP,BATTERY_COOL_EXIT);
/* battery temperature control */
//                                                                  if(BATTERY_MIN_TEMP < BATTERY_COOL_MIN)                 fprintf(LOGFILE," because BATTERY_MIN_TEMP < BATTERY_COOL_MIN        -->  %7.3f < %7.3f\n                                     ",BATTERY_MIN_TEMP,BATTERY_COOL_MIN);
/* coolant temperature control */
                                                                  if(c->batteryStream->tecLast < (B_COOLANT_TARGET - TWO))fprintf(LOGFILE," because TECLAST < (B_COOLANT_TARGET - TWO)         -->  %7.3f < %7.3f\n                                     ",c->batteryStream->tecLast,B_COOLANT_TARGET - TWO);
                                                                  fprintf(LOGFILE,"\n");

                                                                  standbyOrCirculate(simmain);
                                                                  //simmain->circRunTimer = CIRCULATION_TIME_LIMIT + ONE;

                                                                  simmain->chillerMode  = STANDBY_MODE;
                                                                  c->compressorPcnt     = ZERO;
                                                                  c->compressorOnOff    = OFF;
                                                                  c->batteryPumpPcnt    = 0.01;
                                                                  c->bTurnedOn          = NO; 
                                                                  c->inverterPumpPcnt   = 0.01;
                                                                  c->pTurnedOn          = NO;
                                                                  c->fanPcnt            = ZERO;  }


   return ;
}



void heatingMode(struct SimMain *simmain)
{
   struct Chiller  *c = chillerListHead;
   struct Battery  *b = batteryListHead;
   struct Inverter *p = inverterListHead;

   /* do some reporting about why you're entering heating mode */
   if(CHILLER_MODE != HEAT_MODE)
   {
      fprintf(LOGFILE,"\n %6.3f hours:  Entering Heating Mode because ",simTime/3600.0);
//      if(PCS_INLET < PCS_MIN_TEMP)
//         fprintf(LOGFILE,"PCS_INLET < PCS_MIN_TEMP                   --> %7.3f < %7.3f\n",PCS_INLET,PCS_MIN_TEMP);
      if(BATTERY_MAX_TEMP < BATTERY_HEAT_MIN)
         fprintf(LOGFILE,"BATTERY_MAX_TEMP < BATTERY_HEAT_MIN        --> %7.3f < %7.3f\n",BATTERY_MAX_TEMP,BATTERY_HEAT_MIN);
      if(BATTERY_MIN_TEMP < BATTERY_HEAT_TARGET)
         fprintf(LOGFILE,"BATTERY_MIN_TEMP < BATTERY_HEAT_TARGET     --> %7.3f < %7.3f\n",BATTERY_MIN_TEMP,BATTERY_HEAT_TARGET);
   }




   c->heaterPcnt = 0.80; 

   /* can we leave heating mode? */
   if(//(PCS_INLET        > PCS_MAX_TEMP      )  ||
      (BATTERY_MAX_TEMP > BATTERY_HEAT_MAX  )  ||
      (BATTERY_MIN_TEMP > BATTERY_HEAT_EXIT )){   standbyOrCirculate(simmain);
                                                  simmain->chillerMode  = STANDBY_MODE;
                                                  //simmain->circRunTimer = CIRCULATION_TIME_LIMIT + ONE;
                                                  c->compressorPcnt     = ZERO;
                                                  c->compressorOnOff    = OFF;
                                                  c->batteryPumpPcnt    = 0.01;
                                                  c->bTurnedOn          = NO; 
                                                  c->inverterPumpPcnt   = 0.01;
                                                  c->pTurnedOn          = NO;
                                                  c->fanPcnt            = ZERO;  }
   return ;
}


void circulateMode(struct SimMain *simmain)
{
   struct Chiller *c = chillerListHead;

/* does this belong here? */
   if(setPumpCirculation(simmain))  return ;

   c->compressorPcnt    = ZERO;
   c->compressorOnOff   = OFF;
   c->batteryPumpPcnt   = 0.40;
   c->bTurnedOn         = NO; 
   c->inverterPumpPcnt  = 0.40;
   c->pTurnedOn         = NO;
   c->fanPcnt           = ZERO;

   standbyOrCirculate(simmain);   

   return ;
}


/* we're going to do a little check here and either stay in standby or go to circulate mode */
void standbyMode(struct SimMain *simmain)
{
   struct Chiller *c = chillerListHead;
   struct Battery  *b = batteryListHead;
   struct Inverter *p = inverterListHead;


   c->compressorPcnt    = ZERO;
   c->compressorOnOff   = OFF;
   c->batteryPumpPcnt   = 0.01;
   c->bTurnedOn         = NO; 
   c->inverterPumpPcnt  = 0.01;
   c->pTurnedOn         = NO;
   c->fanPcnt           = ZERO;

   standbyOrCirculate(simmain);


   return ;
}


/* this function is used when conditions have been met to leave heating or cooling  */
/* mode.  It will check for uniform temperatures and also if the PCS is moving heat */
/* and set the circulation timer accordingly */
void standbyOrCirculate(struct SimMain *simmain)
{
   struct Chiller *c = chillerListHead;
   struct Battery  *b = batteryListHead;
   struct Inverter *p = inverterListHead;

   /* temps uniform and PCS off? */
   /* if either are NO, go into circulate mode */
   if((abs(BATTERY_MAX_TEMP - BATTERY_MIN_TEMP) > TEMP_STBL)// ||
      /* INVERTER_IS_MOVING_POWER */                           ){   if(CHILLER_MODE != CIRCULATE_MODE)
                                                                   fprintf(LOGFILE," %6.3f hours:  Entering Circulate mode\n",simTime/3600.0);
                                                                CHILLER_MODE          = CIRCULATE_MODE;
                                                                simmain->circRunTimer = ZERO;  }
   else
   {
      if(CHILLER_MODE != STANDBY_MODE)  fprintf(LOGFILE," %6.3f hours:  Entering Standby mode\n",simTime/3600.0);
      simmain->circRunTimer = CIRCULATION_TIME_LIMIT + ONE;
      CHILLER_MODE = STANDBY_MODE;
   }

   return ;
}




void updateChillerConditionAndCool(struct SimMain *simmain)
{
   struct Battery *b = batteryListHead;
   struct Chiller *c = chillerListHead;
   double maxEnthalpyDelta;

   /* update the chiller cold side temperatures */

   /* 1.  Figure out if the chiller is on or not */
   /* 2.  Use the heat transfer rate into the cold plate at the last time step */
   /*     to figure out if the cold side temperature needs adjusted / where    */
   /*     on the power-cold side temperature curve that you are                */
   setRefrigeratedLoopColdHXTemperature(simmain);
   setRefrigeratedLoopPumpSpeed(c);
//   setPCSPumpSpeed(c);


   /* SHARING PERCENTAGE */
   /* sharing percentage is implemented as a percentage of the existing refrigerated loop */
   /* flow rate                                                                           */
   /* calculate the effect of sharing fluid                                               */
   /* how much enthalpy is flowing from the refrigerated loop to the PCS loop             */
   /* how much enthalpy is flowing from the PCS loop to the refrigerated loop             */
   /* the delta is the net enthalpy removed or gained by each                             */   
//   c->sharingEnthalpy = c->sharingPercent*(c->batteryStream->massFlowRate*c->batteryStream->coolantCp*(c->inverterStream->tempEnteringChiller - c->batteryStream->tempLeavingChiller));
   c->sharingEnthalpy = ZERO;

   /* BATTERY COOLANT STREAM CALCULATION */
   /* the heat being removed here is removed from the system, it disappears */
   maxEnthalpyDelta = c->batteryStream->massFlowRate*c->batteryStream->coolantCp*(c->batteryColdSideTemp - c->batteryStream->tecLast);
   c->batteryStream->tempLeavingChiller = c->batteryStream->tecLast 
                                        + (c->heaterPcnt*HEATER_HEAT + c->sharingEnthalpy/(c->batteryStream->massFlowRate*c->batteryStream->coolantCp))
                                        + 0.7*maxEnthalpyDelta/(c->batteryStream->massFlowRate*c->batteryStream->coolantCp);

 

   /* INVERTER COOLANT STREAM CALCULATION */
   /*  the pcs cold side temperature is always ambient                                    */
   /*  and the component of enthalpy sharing with the refrigerated loop is independent of */
   /*  what is happening with the dry cooler part of the loop                             */
   /* the heat being removed here is removed from the system, it disappears */
 //  maxEnthalpyDelta = c->inverterStream->massFlowRate*c->inverterStream->coolantCp*(simmain->ambientTemperature - c->inverterStream->tecLast);
//   c->inverterStream->tempLeavingChiller = c->inverterStream->tecLast + (-c->sharingEnthalpy + 0.2*maxEnthalpyDelta)/(c->inverterStream->massFlowRate*c->inverterStream->coolantCp);


   /* if the control system is not on, let the temperature float */
   /* here, the thermal mass of coolant in the cold plate is 5.0kg each, with cp = 1050 */
   /* heatIntoColdPlate needs a negative sign */

   c->currentAuxPower =   compressorAuxPower(simmain)
                        + c->batPumpPowerPerPcnt*c->batteryPumpPcnt 
                        + c->pcsPumpPowerPerPcnt*c->inverterPumpPcnt 
                        + c->fanAuxPowerPerPcnt*c->fanPcnt 
                        + c->electronicsAuxPower
                        + c->heaterPcnt*HEATER_HEAT;

   /* when control scheme 2 is being used */

   

   return ;
}


void updateHvacConditionAndCool(struct SimMain *simmain)
{
   struct Chiller *c        = chillerListHead;
   struct Hvac *h           = hvacListHead;
   double componentHeatLoad = ZERO;

   /* for the Mallard project, bypass the HVAC, there isn't one */
   if(IS_THERE_AN_HVAC == NO)
   {
      componentHeatLoad  = ZERO;
      h->currentAuxPower = ZERO;
      h->coolingPower    = ZERO;
      return ;
   }


   /* if the system is running */
   /* generate heat inside the ACC, linearly decreasing from 2000.0 W @ 1/2 C */
        if(simmain->current >  0.1)  componentHeatLoad = 5000.0*(simmain->current/150.0);
   else if(simmain->current < -0.1)  componentHeatLoad = 5000.0*(-simmain->current/150.0);
   else                              componentHeatLoad = ZERO;

   /* a UA of 2.0 W/K */
   /* an effective thermal mass of 30.0 kg * 1500 J/kg K */
   h->airTemp += (((simmain->ambientTemperature - h->airTemp)*10.0 + componentHeatLoad)/(30.0*1500.0))*transientDt;
   
   /* if you are above the temperature target + hystersis and the chiller isn't running */
   /* the result sucks if you don't let the HVAC run while the chiller is running */
   if(h->airTemp > (h->temperatureTarget + h->hysteresis))
   {
      h->currentAuxPower = 1600.0;  /* run the HVAC at max power */
      h->coolingPower    = 4000.0;
   }

   if(h->airTemp < h->temperatureTarget)
   {
      h->currentAuxPower = ZERO;
      h->coolingPower    = ZERO;
   }

   h->airTemp -= (h->coolingPower/(40.0*1500.0))*transientDt;

   return ;
}


void updateDehumidifierConditionAndDryOut(struct SimMain *simmain)      /* we're currently not tracking moisture and just running 2 hours a day */
{
   struct Chiller      *c = chillerListHead;
   struct Dehumidifier *d = dehumidifierListHead;

   if((c->fansOnOff == OFF) && (d->cumulativeDehumidifierOnTime < 2.0*CONVERT_HOURS_TO_SECONDS))
   {
      d->currentAuxPower = 500.0;
      d->cumulativeDehumidifierOnTime += transientDt;
   }
   else  d->currentAuxPower = ZERO;



   return ;
}



void updateStateOfCharge(struct SimMain *simmain)
{
   struct Battery *b = batteryListHead;

   /* this was the initlal implementation, before OCV was accounted for */
   //b->soc += 1331.2*12.0*currentCurrent*transientDt/(3600.0*b->totalBatteryEnergy);

   b->soc += currentPower*transientDt /(3600.0*b->totalBatteryEnergy);

   return ;
}


void updateStateOfHealth(struct SimMain *simmain)
{
   struct Battery *b = batteryListHead;
   int i;
   double dSOHdt;
   double aveT = ZERO;

   /* calculate average battery temperature */
//   for(i=0;i<=6;i++) aveT += (b->tempLast[i] - 273.15);
//   aveT = aveT/7.0;

   /* is aging based on the average battery temperature?  or the max? */
   aveT = b->tempLast[6] - 273.15;

   /* calculate the rate of SOH change per year based on the inputs */
   dSOHdt = -2.5 + 7.0*(currentCurrent*currentCurrent/(150.0*150.0))*(-4.5 + 0.228*aveT - 0.00518*aveT*aveT);

   /* adjust this to be per second */
   dSOHdt = dSOHdt/(100.0*365.0*24.0*60.0*60.0);

   /* calculate the change in soh */
   b->soh += dSOHdt*transientDt;


   return ;
}


/* initially this was considered that 18 was the minimum cold side temp */
/* but that doesn't work with the control targets */
void setRefrigeratedLoopColdHXTemperature(struct SimMain *simmain)
{
   struct Chiller *c = chillerListHead;
   struct Battery *b = batteryListHead;
   double maxHeatLoad18,c18,c23;
   int i;

   /* check the heat load on the cold side of the refrigerant loop */



   /* set the temperature of the refrigerant going through the HX with the battery coolant */
   /* based on the cooling curve                                                           */

   /* what do we calculate as the heat flux into the coolant?                              */
   /* a.  if it's less than the max cooling at 18, then set the temperature as 18          */
   /* b.  else, interpolate between cooling curves to find the temperature                 */
   /* c.  things are a little jumpy and I could potentially fix it by having a mass in     */
   /*     between the cold source and the coolant                                          */
   ifTheRefrigeratedLoopIsOn
   {
      if(-b->hicpLast <= (C_COEFF*tableInterpolateCooling(ambientT,c->cooling18)))  c->batteryColdSideTemp += (BASE_COLD_SIDE_TEMPERATURE - c->batteryColdSideTemp)*transientDt/(1.0*910.0);
      else
      {
         c18 = C_COEFF*tableInterpolateCooling(ambientT,c->cooling18);
         c23 = C_COEFF*tableInterpolateCooling(ambientT,c->cooling23);

         
         c->batteryColdSideTemp += ((BASE_COLD_SIDE_TEMPERATURE + (-b->hicpLast - c18)*5.0/(c23-c18)) - c->batteryColdSideTemp)*transientDt/(1.0*910.0);
      }
   }
   else{ c->batteryColdSideTemp = c->batteryStream->tempEnteringChiller; }

   return ;
}



void setRefrigeratedLoopPumpSpeed(struct Chiller *c)
{
   if(c->batteryPumpPcnt < 0.01)  c->batteryPumpPcnt = 0.01;
   c->batteryStream->volumeFlowRate = c->batVolumeFlowRatePerPcnt*c->batteryPumpPcnt;
   c->batteryStream->massFlowRate   = c->batteryStream->volumeFlowRate*1050.0;
   
   return ;
}

/*
void setPCSPumpSpeed(struct Chiller *c)
{
   if(c->inverterPumpPcnt < 0.01) c->inverterPumpPcnt = 0.01;
   c->inverterStream->volumeFlowRate = c->pcsVolumeFlowRatePerPcnt*c->inverterPumpPcnt;
   c->inverterStream->massFlowRate   = c->inverterStream->volumeFlowRate*1050.0;
   return ;
}
*/


double compressorAuxPower(struct SimMain *simmain)
{
   struct Chiller *c = chillerListHead;
   struct Battery *b = batteryListHead;
   double maxCoolingPower;
   double powerScaler;   /* scale aux power by the ratio of heat being moved / max heat capacity */
   int i;
  
   /* find the ambient temperature in the table */ 
   for(i=0;i<=11;i++)  if((simmain->ambientTemperature >= c->cooling18[i][0]) && (simmain->ambientTemperature < c->cooling18[i+1][0]))  break; 
 
   maxCoolingPower = (c->cooling18[i][1] + (simmain->ambientTemperature - c->cooling18[i][0])*(c->cooling18[i+1][1] - c->cooling18[i][1])/(c->cooling18[i+1][0] - c->cooling18[i][0]));

   /* with powerScaler on,    I get 134kW*hrs */
   /*      powerScaler = 1.0, I get 186kW*hrs */
   /*      halfway between,   I get 161kW*hrs */
//   powerScaler = -b->heatIntoColdPlate / maxCoolingPower;
   powerScaler = ((-b->heatIntoColdPlate / maxCoolingPower) + ONE) / TWO;
//   powerScaler = ONE;


    return powerScaler*(c->compressorPcnt)*(c->cooling18[i][2] + (simmain->ambientTemperature - c->cooling18[i][0])*(c->cooling18[i+1][2] - c->cooling18[i][2])/(c->cooling18[i+1][0] - c->cooling18[i][0]));
//   return c->compressorPcnt*(c->cooling18[i][2] + (simmain->ambientTemperature - c->cooling18[i][0])*(c->cooling18[i+1][2] - c->cooling18[i][2])/(c->cooling18[i+1][0] - c->cooling18[i][0]));
}




void tabulateAuxEnergy(struct SimMain *simmain)
{
   struct Chiller      *c = chillerListHead;
   struct Battery      *b = batteryListHead;
   struct AuxLoad      *a = auxLoadListHead;
   struct Hvac         *h = hvacListHead;
   struct Dehumidifier *d = dehumidifierListHead;

   while(c != NULL)
   {
      c->totalAuxEnergy += c->currentAuxPower*transientDt;
      c = NEXT(c);
   }

   while(h != NULL)
   {
      h->totalAuxEnergy += h->currentAuxPower*transientDt;
      h = NEXT(h);
   }

   while(d != NULL)
   {
      d->totalAuxEnergy += d->currentAuxPower*transientDt;
      d = NEXT(d);
   }



   while(a != NULL)
   {
      a->totalAuxEnergy += a->currentAuxPower*transientDt;
      a = NEXT(a);
   }

   /* split-out the aux energy into operating, resting, and idling                          */
   /*  1. OPERATING - when the chiller is on                                                */
   /*  2. RESTING   - when the chiller is off and battery temperature is above the cutoff   */
   /*  3. IDLING    - when the chiller is off and battery temperature is below the cutoff   */
   a = auxLoadListHead;   b = batteryListHead;   c = chillerListHead;   h = hvacListHead;   d = dehumidifierListHead;


   if(b->temperature[6] > b->maxBatteryTemp){ b->maxBatteryTemp = b->temperature[6]; }

   if((c->currentAuxPower + h->currentAuxPower + d->currentAuxPower + a->currentAuxPower) > simmain->peakAuxPower)
      simmain->peakAuxPower = (c->currentAuxPower + h->currentAuxPower + d->currentAuxPower + a->currentAuxPower);


   if((currentCurrent*currentCurrent > 0.001))
   {   c->operatingAuxEnergy      += (c->currentAuxPower + h->currentAuxPower + d->currentAuxPower + a->currentAuxPower)*transientDt;
       b->battAveTempOperating    += b->temperature[6]*transientDt;
       c->timeSpentOperating      += transientDt; }
   else if(b->temperature[6] > idleRestCutoffTemp)
   {   c->restingAuxEnergy        += (c->currentAuxPower + h->currentAuxPower + d->currentAuxPower + a->currentAuxPower)*transientDt;
       b->battAveTempNotOperating += b->temperature[6]*transientDt;
       c->timeSpentResting        += transientDt; }
   else
   {   c->idlingAuxEnergy         += (c->currentAuxPower + h->currentAuxPower + d->currentAuxPower + a->currentAuxPower)*transientDt;
       b->battAveTempNotOperating += b->temperature[6]*transientDt;
       c->timeSpentIdling         += transientDt; }

   return ;
}



void copyCurrentTimeValuesToPreviousTimeValues(struct SimMain *simmain)
{
   struct Chiller  *c = simmain->c;
   struct Battery  *b = simmain->b;
//   struct Inverter *p = simmain->i;
   int i;

   prevT_internal             = nextT_internal;
   c->batteryStream->tlcLast  = c->batteryStream->tempLeavingChiller;
   c->batteryStream->tecLast  = c->batteryStream->tempEnteringChiller;
//   c->inverterStream->tlcLast = c->inverterStream->tempLeavingChiller;
//   c->inverterStream->tecLast = c->inverterStream->tempEnteringChiller;
//   p->tempLast                = p->temperature;

   b->hicpLast = b->heatIntoColdPlate;


   for(i=0;i<=6;i++)
   {
      wall1Tlast(i) = wall1T(i);
      wall2Tlast(i) = wall2T(i);
   }

   return ;
}


int setPumpCirculation(struct SimMain *simmain)
{
   struct Chiller *c = chillerListHead;

   /* check if the pumps have been off too long                      */
   /* if yes, then set the circulation timer to zero so that it gets */
   /* picked up on the next line and everything turns on             */
//   if(simmain->cameFromStandby)  simmain->circRunTimer += dt;
//   if(TIME_SINCE_PUMPS_HAVE_BEEN_OFF > MAX_PUMP_OFF_TIME) simmain->circRunTimer = ZERO;
   

   if(simmain->circRunTimer < CIRCULATION_TIME_LIMIT){ simmain->circRunTimer += transientDt;
                                                       c->batteryPumpPcnt                = 0.40;
                                                       c->batteryStream->volumeFlowRate  = c->batteryPumpPcnt*480.0/60000.0;
                                                       c->batteryStream->massFlowRate    = c->batteryStream->volumeFlowRate*1050.0;
                                                      // c->inverterPumpPcnt               = 0.30;
                                                      // c->inverterStream->volumeFlowRate = c->inverterPumpPcnt*240.0/60000.0;
                                                      // c->inverterStream->massFlowRate   = c->inverterStream->volumeFlowRate*1050.0;
                                                       return 1; }


   /* if the pumps don't need to be on because of a circulation condition, return 0 */
   return 0;
}


double addToAverageBatteryTemperature(struct SimMain *simmain)
{
   struct Battery *b = batteryListHead;
   double ttt;
   int i;

   ttt = ZERO;

   for(i=0;i<=6;i++)  ttt += b->temperature[i];

   return ttt;
}


void writeOutputFileHeader(struct SimMain *simmain)
{
   struct Chiller      *c = chillerListHead;
   struct Inverter     *p = inverterListHead;
   struct Battery      *b = batteryListHead;
   struct AuxLoad      *a = auxLoadListHead;
   struct Hvac         *h = hvacListHead;
   struct Dehumidifier *d = dehumidifierListHead;
   int i;


   fprintf(OUTPUTFILE," It  Time(s)  Current(A)  SOC  chillerMode  batDemand  pcsDemand  sharingPcnt  compressorSetPcnt  FanSetPcnt");


   /* flow rates */
   fprintf(OUTPUTFILE," Bat_Pump_Pcnt Bat_Flow_Rate(LPM)");
   if(p != NULL) fprintf(OUTPUTFILE," PCS_Pump_Pcnt PCS_Flow_Rate(LPM)");


   /* report aux power use */
   while(a != NULL){ fprintf(OUTPUTFILE," Aux_Load_Power(kW)");     a = NEXT(a); }
   while(c != NULL){ fprintf(OUTPUTFILE," Chiller_Aux_Power(kW)");  c = NEXT(c); }
   while(p != NULL){ fprintf(OUTPUTFILE," Inverter_Aux_Power(kW)"); p = NEXT(p); }
   while(h != NULL){ fprintf(OUTPUTFILE," HVAC_Aux_Power(W)");      h = NEXT(h); }
   while(d != NULL){ fprintf(OUTPUTFILE," DH_Aux_Power(W)");        d = NEXT(d); }
   fprintf(OUTPUTFILE," Total_Aux_Power(W)");

   a = auxLoadListHead;  c = chillerListHead;   h = hvacListHead;   d = dehumidifierListHead;  p = inverterListHead;

   /* report cumulative aux energy use */
   while(a != NULL){ fprintf(OUTPUTFILE," Aux_Load_Energy(kW*hrs)");     a = NEXT(a); }
   while(c != NULL){ fprintf(OUTPUTFILE," Chiller_Aux_Energy(kW*hrs)");  c = NEXT(c); }
   while(p != NULL){ fprintf(OUTPUTFILE," Inverter_Aux_Energy(kW*hrs)"); p = NEXT(p); }
   while(h != NULL){ fprintf(OUTPUTFILE," HVAC_Aux_Energy(kW*hrs)");     h = NEXT(h); }
   while(d != NULL){ fprintf(OUTPUTFILE," DH_Aux_Energy(kW*hrs)");       d = NEXT(d); }
   fprintf(OUTPUTFILE," Total_Aux_Energy(kW*hrs)");

   /* report other fluxes */
//   fprintf(OUTPUTFILE," Cell_Heat_Gen_(W) InverterHeat(W) Battery_Cold_Plate_Flux(W) PCS_Cold_Plate_Flux(W) Sharing_Enthalpy(W)");
   fprintf(OUTPUTFILE," Cell_Heat_Gen_(W) Battery_Cold_Plate_Flux(W) Sharing_Enthalpy(W)");



   /* report temperatures */
   c = chillerListHead;   h = hvacListHead;   d = dehumidifierListHead;   p = inverterListHead;
   fprintf(OUTPUTFILE," Ambient_Temp(C) Internal_Air_Temp(C)");
   fprintf(OUTPUTFILE," Bat_Coolant_Temp_Leaving_Chiller(C) Bat_Coolant_Temp_Entering_Chiller(C)");
   while(p != NULL){  fprintf(OUTPUTFILE," PCS_CoolantTemp_Leaving_Chiller(C) PCS_Coolant_Temp_Entering_Chiller(C)");  p = NEXT(p); }

   p = inverterListHead;

   while(b != NULL){ for(i=0;i<=6;i++)   fprintf(OUTPUTFILE," Bat_temp_%i",i);     b = NEXT(b);  }
   while(p != NULL){ fprintf(OUTPUTFILE," Inverter_Temp(C)");                      p = NEXT(p);  }
   while(h != NULL){ fprintf(OUTPUTFILE," HVAC_Air_Temp(C)");                      h = NEXT(h);  }

   
   /* report other things */
   b = batteryListHead;  c = chillerListHead;
   while(d != NULL){ fprintf(OUTPUTFILE," DH_OnTime(hrs)");                  d = NEXT(d);  }
   while(b != NULL){ fprintf(OUTPUTFILE," Cumulative_Battery_Heat(kW*hrs)"); b = NEXT(b);  }
   fprintf(OUTPUTFILE," Cumulative_Ambient_Heat_Exchange(kW*hrs)");

   fprintf(OUTPUTFILE," RadiationLoad(W) Outer_Surface_Temp(C)");


   fprintf(OUTPUTFILE,"\n");

   return ;
}



void outputTimeStepResults(struct SimMain *simmain)
{
   struct Chiller      *c = chillerListHead;
   struct Battery      *b = batteryListHead;
   struct AuxLoad      *a = auxLoadListHead;
   struct Hvac         *h = hvacListHead;
   struct Inverter     *p = inverterListHead;
   struct Dehumidifier *d = dehumidifierListHead;
   double aPower, aEnergy;
   double cPower, cEnergy;
   double pPower, pEnergy;
   double hPower, hEnergy;
   double dPower, dEnergy;
   int i;


   fprintf(OUTPUTFILE," %i  %8.2f %e %6.3f %2i %6.3f %6.3f %6.2f",Iteration,simTime,currentCurrent,b->soc,CHILLER_MODE,bDemand,pDemand,c->sharingPercent);
   /* compressor set percent, fan set percent */
   fprintf(OUTPUTFILE," %6.2f %6.2f",c->compressorPcnt,c->fanPcnt);

   /* flow rates */
   fprintf(OUTPUTFILE," %f %f",c->batteryPumpPcnt,c->batVolumeFlowRatePerPcnt*c->batteryPumpPcnt*M3_PER_SECOND_TO_LPM);


   /* report aux power use */
   aPower = ZERO;  cPower = ZERO;  pPower = ZERO;  hPower = ZERO;  dPower = ZERO;
   while(a != NULL){ fprintf(OUTPUTFILE," %f",a->currentAuxPower);  aPower += a->currentAuxPower;  a = NEXT(a); }
   while(c != NULL){ fprintf(OUTPUTFILE," %f",c->currentAuxPower);  cPower += c->currentAuxPower;  c = NEXT(c); }
   while(p != NULL){ fprintf(OUTPUTFILE," %f",p->currentAuxPower);  pPower += p->currentAuxPower;  p = NEXT(p); }
   while(h != NULL){ fprintf(OUTPUTFILE," %f",h->currentAuxPower);  hPower += h->currentAuxPower;  h = NEXT(h); }
   while(d != NULL){ fprintf(OUTPUTFILE," %f",d->currentAuxPower);  dPower += d->currentAuxPower;  d = NEXT(d); }
   fprintf(OUTPUTFILE," %f",aPower + cPower + pPower + hPower + dPower);



   /* report cumulative aux energy use */
   a = auxLoadListHead;   c = chillerListHead;   h = hvacListHead;   d = dehumidifierListHead;  p = inverterListHead;
   aEnergy = ZERO;        cEnergy = ZERO;        hEnergy = ZERO;     dEnergy = ZERO;            pEnergy = ZERO;
   while(a != NULL){ fprintf(OUTPUTFILE," %f",a->totalAuxEnergy*JOULES_TO_KW_HOURS);  aEnergy += a->totalAuxEnergy;  a = NEXT(a); }
   while(c != NULL){ fprintf(OUTPUTFILE," %f",c->totalAuxEnergy*JOULES_TO_KW_HOURS);  cEnergy += c->totalAuxEnergy;  c = NEXT(c); }
   while(p != NULL){ fprintf(OUTPUTFILE," %f",p->totalAuxEnergy*JOULES_TO_KW_HOURS);  pEnergy += p->totalAuxEnergy;  p = NEXT(p); }
   while(h != NULL){ fprintf(OUTPUTFILE," %f",h->totalAuxEnergy*JOULES_TO_KW_HOURS);  hEnergy += h->totalAuxEnergy;  h = NEXT(h); }
   while(d != NULL){ fprintf(OUTPUTFILE," %f",d->totalAuxEnergy*JOULES_TO_KW_HOURS);  dEnergy += d->totalAuxEnergy;  d = NEXT(d); }
   fprintf(OUTPUTFILE," %f",(aEnergy + cEnergy + hEnergy + dEnergy + pEnergy)*JOULES_TO_KW_HOURS);
   simmain->totalAuxEnergy = (aEnergy + cEnergy + hEnergy + dEnergy + pEnergy)*JOULES_TO_KW_HOURS;



   /* report other heats and fluxes */
   a = auxLoadListHead;   c = chillerListHead;   p = inverterListHead;  h = hvacListHead;   d = dehumidifierListHead;
   fprintf(OUTPUTFILE," %e",batteryTabHeat + batteryTotalHeatGeneration(simmain));
//   fprintf(OUTPUTFILE," %e %e %e %e",p->inverterHeat,b->heatIntoColdPlate,p->heatIntoColdPlate,c->sharingEnthalpy);
   fprintf(OUTPUTFILE," %e %e",b->heatIntoColdPlate,c->sharingEnthalpy);




   /* report temperatures */
   a = auxLoadListHead;   b = batteryListHead;   c = chillerListHead;   h = hvacListHead;   d = dehumidifierListHead;   p = inverterListHead;
   fprintf(OUTPUTFILE," %8.3f %8.3f",simmain->ambientTemperature - 273.15,simmain->internalAirTemp - 273.15);
   fprintf(OUTPUTFILE," %8.3f %8.3f",c->batteryStream->tempLeavingChiller,c->batteryStream->tempEnteringChiller);
   while(p != NULL){ fprintf(OUTPUTFILE," %8.3f %8.3f",c->inverterStream->tempLeavingChiller,c->inverterStream->tempEnteringChiller); p = NEXT(p); }
   while(b != NULL){  for(i=0;i<=6;i++)   fprintf(OUTPUTFILE," %8.3f",b->temperature[i]);    b = NEXT(b);  }
  
   p = inverterListHead; 
   while(p != NULL){ fprintf(OUTPUTFILE," %f",p->temperature);                               p = NEXT(p);  }
   while(h != NULL){ fprintf(OUTPUTFILE," %f",h->airTemp);                                   h = NEXT(h);  }
   while(d != NULL){ fprintf(OUTPUTFILE," %f",d->cumulativeDehumidifierOnTime/3600.0);       d = NEXT(d);  }

   b = batteryListHead;
   while(b != NULL){  fprintf(OUTPUTFILE," %e",b->cumulativeBatteryHeat/(1000.0*3600.0));    b = NEXT(b);  }
   fprintf(OUTPUTFILE," %e",simmain->totalAmbientHeatExchange/(1000.0*3600.0));

   fprintf(OUTPUTFILE," %e %e",simmain->radiationLoad,wall1T(6));


   fprintf(OUTPUTFILE,"\n");

   return ;
}


void writeFinalOutputToScreen(struct SimMain *simmain)
{
   struct Battery      *b = batteryListHead;
   struct Chiller      *c = chillerListHead;
   struct Inverter     *p = inverterListHead;
   struct Hvac         *h = hvacListHead;
   struct Dehumidifier *d = dehumidifierListHead;
   struct AuxLoad      *a = auxLoadListHead;
   int i = 1;


   printf("\n *** RUN SUMMARY ***\n\n");
   printf(" AVERAGE AMBIENT TEMPERATURE:     %7.2f degrees C\n\n",(simmain->ambientTempSum/Iteration) - 273.15);
   printf(" BATTERY HEAT GENERATED:          %7.2f kW*hrs\n",b->cumulativeBatteryHeat/(3600.0*1000.0));
   printf(" HEAT EXCHANGE WITH AMBIENT AIR:  %7.2f kW*hrs\n",simmain->totalAmbientHeatExchange/(3600.0*1000.0));
   printf(" RADIATION HEAT LOAD:             %7.2f kW*hrs\n\n",simmain->totalRadiationHeatExchange/(3600.0*1000.0));
   printf(" AUX ENERGY USED:                 %7.2f kW*hrs\n",simmain->totalAuxEnergy);
   printf("   OPERATING AUX:                 %7.2f kW*hrs   (%5.2f hours operating)\n",c->operatingAuxEnergy*JOULES_TO_KW_HOURS,c->timeSpentOperating/3600.0);
   printf("     RESTING AUX:                 %7.2f kW*hrs   (%5.2f hours resting)\n",c->restingAuxEnergy*JOULES_TO_KW_HOURS,c->timeSpentResting/3600.0);
   printf("      IDLING AUX:                 %7.2f kW*hrs   (%5.2f hours idling)\n\n",c->idlingAuxEnergy*JOULES_TO_KW_HOURS,c->timeSpentIdling/3600.0);

   printf("   CHILLER AUX:                   %7.2f kW*hrs",c->totalAuxEnergy*JOULES_TO_KW_HOURS);
   printf("   (%5.2f Chiller COP)\n",(b->cumulativeBatteryHeat + simmain->totalAmbientHeatExchange)/c->totalAuxEnergy);
   while(h != NULL){ printf("   HVAC AUX:                      %7.2f kW*hrs\n",h->totalAuxEnergy*JOULES_TO_KW_HOURS);    h = NEXT(h);             }
   while(d != NULL){ printf("   DEHUMIDIFIER AUX:              %7.2f kW*hrs\n",d->totalAuxEnergy*JOULES_TO_KW_HOURS);    d = NEXT(d);             }
   while(a != NULL){ printf("   AUX LOAD %2i:                   %7.2f kW*hrs\n\n",i,a->totalAuxEnergy*JOULES_TO_KW_HOURS);  a = NEXT(a);    i += 1; }

   printf(" PEAK AUX POWER:                  %7.2f kW\n",simmain->peakAuxPower/1000.0);
   printf(" MAX BATTERY TEMP:                %7.2f degrees C\n",b->maxBatteryTemp-273.15);
   printf(" AVERAGE BATTERY TEMP:            %7.2f degrees C\n",((b->battAveTempOperating+b->battAveTempNotOperating)/(c->timeSpentOperating+c->timeSpentResting+c->timeSpentIdling))-273.15);
   if(c->timeSpentOperating > 0.00001) printf(" OPERATING AVERAGE BATTERY TEMP:  %7.2f degrees C\n",(b->battAveTempOperating/c->timeSpentOperating)-273.15);
   else printf(" OPERATING AVERAGE BATTERY TEMP:    ----- degrees C\n");
   printf(" REST/IDLE AVERAGE BATTERY TEMP:  %7.2f degrees C\n\n",(b->battAveTempNotOperating/(c->timeSpentResting+c->timeSpentIdling))-273.15);

   printf(" INITIAL SOH:                     %7.2f\n",b->initialSoh*100.0);
   printf(" END-OF-YEAR SOH (directional):   %7.2f\n\n",100.0*(b->initialSoh - (365.0*(b->initialSoh - b->soh))));
   printf("\n");


   i = 1;
   a = auxLoadListHead;   b = batteryListHead;   c = chillerListHead;   h = hvacListHead;   d = dehumidifierListHead;   p = inverterListHead;
   fprintf(LOGFILE,"\n\n *** RUN SUMMARY ***\n\n");
   fprintf(LOGFILE," AVERAGE AMBIENT TEMPERATURE:     %7.2f degrees C\n\n",(simmain->ambientTempSum/Iteration) - 273.15);
   fprintf(LOGFILE," BATTERY HEAT GENERATED:          %7.2f kW*hrs\n",b->cumulativeBatteryHeat/(3600.0*1000.0));
   fprintf(LOGFILE," HEAT EXCHANGE WITH AMBIENT AIR:  %7.2f kW*hrs\n",simmain->totalAmbientHeatExchange/(3600.0*1000.0));
   fprintf(LOGFILE," RADIATION HEAT LOAD:             %7.2f kW*hrs\n\n",simmain->totalRadiationHeatExchange/(3600.0*1000.0));
   fprintf(LOGFILE," AUX ENERGY USED:                 %7.2f kW*hrs\n",simmain->totalAuxEnergy);
   fprintf(LOGFILE,"   OPERATING AUX:                 %7.2f kW*hrs\n",c->operatingAuxEnergy*JOULES_TO_KW_HOURS);
   fprintf(LOGFILE,"     RESTING AUX:                 %7.2f kW*hrs\n",c->restingAuxEnergy*JOULES_TO_KW_HOURS);
   fprintf(LOGFILE,"      IDLING AUX:                 %7.2f kW*hrs\n\n",c->idlingAuxEnergy*JOULES_TO_KW_HOURS);

   fprintf(LOGFILE,"   CHILLER AUX:                   %7.2f kW*hrs",c->totalAuxEnergy*JOULES_TO_KW_HOURS);
   fprintf(LOGFILE,"   (%4.2f Chiller COP)\n",(b->cumulativeBatteryHeat + simmain->totalAmbientHeatExchange)/c->totalAuxEnergy);
   while(h != NULL){ fprintf(LOGFILE,"   HVAC AUX:                      %7.2f kW*hrs\n",h->totalAuxEnergy*JOULES_TO_KW_HOURS);    h = NEXT(h);             }
   while(d != NULL){ fprintf(LOGFILE,"   DEHUMIDIFIER AUX:              %7.2f kW*hrs\n",d->totalAuxEnergy*JOULES_TO_KW_HOURS);    d = NEXT(d);             }
   while(a != NULL){ fprintf(LOGFILE,"   AUX LOAD %2i:                   %7.2f kW*hrs\n\n",i,a->totalAuxEnergy*JOULES_TO_KW_HOURS);  a = NEXT(a);    i += 1; }


   fprintf(LOGFILE," PEAK AUX POWER:                  %7.2f kW\n",simmain->peakAuxPower/1000.0);
   fprintf(LOGFILE," MAX BATTERY TEMP:                %7.2f degrees C\n",b->maxBatteryTemp-273.15);
   fprintf(LOGFILE," AVERAGE BATTERY TEMP:            %7.2f degrees C\n",((b->battAveTempOperating+b->battAveTempNotOperating)/(c->timeSpentOperating+c->timeSpentResting+c->timeSpentIdling))-273.15);
   if(c->timeSpentOperating > 0.00001) fprintf(LOGFILE," OPERATING AVERAGE BATTERY TEMP:  %7.2f degrees C\n",(b->battAveTempOperating/c->timeSpentOperating)-273.15);
   else fprintf(LOGFILE," OPERATING AVERAGE BATTERY TEMP:    ----- degrees C\n");
   fprintf(LOGFILE," REST/IDLE AVERAGE BATTERY TEMP:  %7.2f degrees C\n\n",(b->battAveTempNotOperating/(c->timeSpentResting+c->timeSpentIdling))-273.15);



   fprintf(LOGFILE," INITIAL SOH:                     %7.2f\n",b->initialSoh*100.0);
   fprintf(LOGFILE," END-OF-YEAR SOH (directional):   %7.2f\n\n",100.0*(b->initialSoh - (365.0*(b->initialSoh - b->soh))));
   fprintf(LOGFILE,"\n");

   return ;
}





