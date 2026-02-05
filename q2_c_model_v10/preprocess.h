

/* SYSTEM CONFIGURATION */

/* sunrise and sunset times, to drive the radiation model */
#define RADIATION_ON_OFF                    simmain->radiationModelOnOrOff

#define IS_THERE_AN_HVAC                    0

/* total system energy in megawatt-hours */
#define TOTAL_SYSTEM_ENERGY                 4.07

/* max rate of charge or discharge of this system      */
/* 4 hours to do a charge -> this number is 0.25       */
/* 2 hours to do a charge -> this number is 0.50, etc. */
#define SYSTEM_POWER_RATE                   0.50





#define ZERO                                0.000000000000
#define HALF                                0.500000000000
#define ONE                                 1.000000000000
#define TWO                                 2.000000000000

#define NO_INPUT                            -999999.0

#define YES                                 1
#define NO                                  0

#define ON                                  1
#define OFF                                 0

#define STEFAN_BOLTZMANN_CONSTANT           0.000000056704
#define TO_THE_FOURTH(x)                    (x*x*x*x)


#define JOULES_TO_KW_HOURS                  0.00000027777777778
#define CONVERT_HOURS_TO_SECONDS            3600.00000000000000
#define M3_PER_SECOND_TO_LPM                60000.0000000000000
#define MEGAWATTS_TO_WATTS                  1000000.00000000000


/* SIMMAIN preprocessors */

#define simTime                             simmain->currentTime
#define transientDt                         simmain->dt
#define simulationMaxDuration               simmain->tMax
#define Iteration                           simmain->simIteration
#define reportingIt                         simmain->resultOutputFrequency


#define ambientT                            simmain->ambientTemperature
#define OUTPUTFILE                          simmain->outFile
#define INPUTFILE                           simmain->inFile
#define LOGFILE                             simmain->logFile
#define currentCurrent                      simmain->current
#define currentPower                        simmain->currentSystemPower
#define maxChargePower                      simmain->cRate
#define maxDischargePower                   simmain->dRate

/* wall 1 is the wall NOT exposed to solar radiation */
/* wall 2 is the wall exposed to solar radiation     */
#define wall1T(x)                           simmain->tw1->temp[x]
#define wall1Tlast(x)                       simmain->tw1->tempLast[x]
#define wall1K                              simmain->tw1->conductivity
#define wall1dx                             simmain->tw1->dx
#define wall1OuterUA                        simmain->tw1->outerUA
#define wall1InnerUA                        simmain->tw1->innerUA
#define steelArea                           simmain->tw1->area
#define wall2T(x)                           simmain->tw2->temp[x]
#define wall2Tlast(x)                       simmain->tw2->tempLast[x]
#define wall2K                              simmain->tw2->conductivity
#define wall2dx                             simmain->tw2->dx
#define wall2OuterUA                        simmain->tw2->outerUA
#define wall2InnerUA                        simmain->tw2->innerUA
#define insulationArea                      simmain->tw2->area



#define prevT_internal                      simmain->internalAirTempPrev
#define nextT_internal                      simmain->internalAirTemp

#define numberofHvTransformers              3
#define numberOfMvTransformers              10



#define NEXT(a)                             a->next


#define tableOffset                         102


#define batteryListHead                     simmain->b
#define chillerListHead                     simmain->c
#define hvacListHead                        simmain->h
#define inverterListHead                    simmain->i
#define dehumidifierListHead                simmain->d
#define auxLoadListHead                     simmain->a
#define currentProfileListHead              simmain->cProfile
#define powerProfileListHead                simmain->pProfile
#define tempProfileListHead                 simmain->tProfile
#define thermalWallListHead                 simmain->tw



/* BATTERY preprocessors */


/* CHILLER preprocessors */

enum controlModes {AUTO_MODE,
                   COOL_MODE,
                   HEAT_MODE,
                   CIRCULATE_MODE,
                   STANDBY_MODE};


/* these coefficients scale the cooling power and the aux power */
/* of the chiller, respectively                                 */
#define C_COEFF                             1.000
#define A_COEFF                             1.000

#define CHILLER_MODE                        simmain->chillerMode

/* cutoff temperatures for reporting split-out aux values */
#define idleRestCutoffTemp                  296.15

#define inverterMinimumTriggerTemp          290.15
#define batteryMinimumTriggerTemp           288.15

/* the maximum time that the pumps are allowed to be off is 45 minutes, expressed below in seconds */
#define MAX_PUMP_OFF_TIME                   2700.0
#define TIME_SINCE_PUMPS_HAVE_BEEN_OFF      simmain->circRunTimer

/* circulation mode will run for 2 minutes, expressed below in seconds */
#define CIRCULATION_TIME_LIMIT              120.0

/* max and min battery temperature currently refer to the same thing */
/* since the model is not set up to accommodate variation in this    */
#define BATTERY_MAX_TEMP                    b->temperature[6]
#define BATTERY_MIN_TEMP                    b->temperature[6]
#define BATTERY_COOL_MAX                    298.15
//#define BATTERY_COOL_TARGET                 293.15
#define BATTERY_COOL_TARGET                 298.15

#define B_COOLANT_TARGET                    296.15

/* when this is 17, we never get there because of the coolant temperature */
//#define BATTERY_COOL_MIN                    290.15
#define BATTERY_COOL_EXIT                   295.15
/* this lets you exit cooling in a more normal way */
//#define BATTERY_COOL_MIN                    294.15
#define BATTERY_COOL_MIN                    292.65


#define BATTERY_HEAT_MAX                    295.15
#define BATTERY_HEAT_TARGET                 291.15
#define BATTERY_HEAT_MIN                    288.15
#define BATTERY_HEAT_EXIT                   290.65

#define PCS_SENSITIVITY                     2.0
#define TEMP_STBL                           3.0

#define PCS_COOL_TARGET                     323.15
//#define PCS_COOL_TARGET                     (((ambientT + 15.0) > 326.15) ? 326.15 : (ambientT + 15.0))
#define PCS_FLOW_TEMP                       313.15
#define PCS_INLET                           c->inverterStream->tlcLast
//#define PCS_MAX_TEMP                        /* depends on ambient temperature */
#define PCS_MAX_TEMP                        323.15
#define PCS_MIN_TEMP                        288.15


#define BATTERY_FLOW_0P25                   1.000
//#define BATTERY_FLOW_0P25                   1.0000.72
#define BATTERY_FLOW_0P50                   0.90

#define PCS_FLOW_LOW                        0.38
#define PCS_FLOW_HIGH                       0.43

/* minimum chiller compressor run time, hours */
#define MIN_COMPRESSOR_RUN_TIME             0.25

/* these are the cold side temperatures happening in the refrigerated loop in the chiller */
/* the upper one should be base + 5.0                                                     */
#define BASE_COLD_SIDE_TEMPERATURE          292.15
#define UPPER_COLD_SIDE_TEMPERATURE         293.15


#define INVERTER_IS_MOVING_POWER            (p->inverterHeat > 0.01)
#define CURRENT_IS_MOVING                   ((simmain->current*simmain->current) > 0.01)

#define bDemand                             c->batteryDemand
#define pDemand                             c->pcsDemand
#define bSensitivity                        c->batterySensitivity
#define pSensitivity                        c->inverterSensitivity
#define sharingTempThreshold                c->sharingTemperatureThreshold

/* the heater in the chiller can generate 18kW */
#define HEATER_HEAT                         18000.0

/* circulate the pumps if they have been off for more than 1800s/30 minutes */
#define maxBattPumpOffTime                  1800.0
#define maxPcsPumpOffTime                   1800.0

#define turnOnRefrigerantLoop               { c->refLoopPcnt = bDemand;  c->batteryPumpPcnt = ONE;  c->bTurnedOn = YES; }

#define anyCoolingIsOn                      (c->bTurnedOn == ON)  || (c->pTurnedOn == ON)
#define allCoolingIsOff                     (c->bTurnedOn == OFF) && (c->pTurnedOn == OFF)


/* battery tab heat is considered to be 2.5W per cell @ 0.5C */
/*    and to linearly decrease from that point               */
#define batteryTabHeat                      ((currentCurrent > 0.0) ? (2.5*104.0*48.0*(currentCurrent/150.0)) : (-2.5*104.0*48.0*(currentCurrent/150.0)))
#define batteryHeatMultiplier               1.0
#define numberOfQuantums                    58.0


/* other preprocessing */
#define ifTheChillerIsOn                    if(c->fansOnOff == ON)
#define ifTheRefrigeratedLoopIsOn           if(c->compressorOnOff == ON)
#define ifTheRefrigeratedLoopPumpIsRunning  if(c->batteryPumpOnOff == ON)
#define ifThePCSPumpIsRunning               if(c->inverterPumpOnOff == ON)


#define chargeOrDischargeIsHappening        ((simmain->current > 0.001) || (simmain->current < -0.001))

#define heat(x,y)                           b->cellHeat[x][y]

enum Emain { FIXED_AMB_TEMP, INITIAL_TEMP, MAX_CHARGE_RATE, MAX_DISCHARGE_RATE, CHILLER_MODEL, CHILLER_NOISE_KIT, BATTERY_MODEL, HVAC_OPTION_PRESENT, TIME_OF_SUNRISE, TIME_OF_SUNSET, BATTERY_LIFE, INITIAL_SOC, POWER_FILE_NAME , IN_ANYmain };
