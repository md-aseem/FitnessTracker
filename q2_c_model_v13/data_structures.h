

#include <stdio.h>


typedef struct SimMain
{
   char   chillerModelName[128];
   char   chillerNoiseKit[128];
   char   batteryModelName[128];
   char   hvacPresent[128];
   char   maxCRate[16];

   double cRate;
   double dRate;

   double tMax;
   double currentTime;
   double dt;

   int    chillerMode;
   int    cameFromStandby;
   int    hvacYesOrNo;

   char   powerFileName[128];
   double maxSystemPower;       /* for limiting operating power */
   double currentSystemPower;
   double peakAuxPower;         /* to record peak power during a run */

   double initialTemperature;
   double ambientTemperature;
   int    radiationModelOnOrOff;
   double radiationLoad;
   double radiationSurfaceArea;
   double ambientTempSum;
   double current;

   char   batteryLifeStatus[32];
   double bol_eol;
   double cellsPerModule;
   double modulesPerQuantum;

   double sunriseTime;
   double sunsetTime;

   /* not ideal, but container information is here */
   double internalAirTemp, internalAirTempPrev;
   double containerWallUA;
   double containerWallArea;
   double containerWallPcntSteel;
   double totalAmbientHeatExchange;
   double totalRadiationHeatExchange;
   double pcntSurfaceInRadiation;
   double radiationIntensity;

   double circRunTimer;

   /* store high level simulation information */
   double totalAuxEnergy;

   int    simIteration;
   int    resultOutputFrequency;

   FILE   *cRateInputFile;
   FILE   *powerInputFile;
   FILE   *inFile;
   FILE   *outFile;
   FILE   *logFile;

   struct CDCycle      *cycle;

   struct ThermalWall  *tw1;
   struct ThermalWall  *tw2;

   struct Chiller      *c;
   struct Battery      *b;
   struct Inverter     *i;
   struct Hvac         *h;
   struct Dehumidifier *d;
   struct AuxLoad      *a;  /* a list of constant aux loads */

   struct TimeHistory  *th; /* a tag to remember the last used element of a time history table */
                            /* this is used to speed up the current table lookup               */

   struct TimeHistory  *pProfile;
   struct TimeHistory  *powerFileTag;

   struct TimeHistory  *cProfile;
   struct TimeHistory  *currentFileTag;  /* to keep track of the last time step that the simulation is at */
                                         /* within the list of current profile elements                   */
   struct TimeHistory  *tProfile;
   struct TimeHistory  *tempFileTag;     /* to keep track of the last time step that the simulation is at */
                                         /* within the list of current profile elements                   */


} OSimMain, *pSimMain;


typedef struct CDCycle
{
   double startTime;
   double targetSoc1;
   double waitTime;
   double targetSoc2;

   double endTime1;
   double startTime2;
   double endTime2;

   double power1;
   double power2;

   struct CDCycle *next;

} OCDCycle, *pCDCycle;



typedef struct Chiller
{


   /* the total amount of aux energy is added up, along with:                   */
   /*                                                                           */
   /*  operatingAuxEnergy -> energy used while the chiller is operating or      */
   /*                        if the battery temperature is above 23 degrees C   */
   /*  restingAuxEnergy   -> energy used while the battery temperature is above */
   /*                        23 degrees C while the chiller is not operating    */
   /*  idleAuxEnergy      -> all other energy used                              */
   /*                                                                           */
   double totalAuxEnergy;
   double operatingAuxEnergy;
   double restingAuxEnergy;
   double idlingAuxEnergy;

   double timeSpentOperating;
   double timeSpentResting;
   double timeSpentIdling;


   double circulationTimer;
   double pumpOffTimer;


   /* coefficient of pump and compressor caps */
   /* in particular, this is for the Q2.0, which has the same chiller hardware */
   /* but uses different caps based on it being a 0.25C or 0.50C system        */
   double pumpAuxCap;
   double compAuxCap;
   double coolingPowerCoeff;


   /* tables of ambient temperature in column 1          */
   /*    and cooling power, COP, and aux use in column 2 */
   /* there is one at 18 degrees C cold side temperature */
   /* and another at 23 degrees C cold side temperature  */
   double cooling18[12][3];
   double cooling23[12][3];

   double batteryTemperatureTarget;
   double inverterTemperatureTarget;
   double batteryDemand;
   double pcsDemand;
   double batterySensitivity;
   double inverterSensitivity;


   /* keep a time since the pcs or battery loop last ran                       */
   /* if it hasn't run for some duration, then run it for a time to keep       */
   /* temperatures fairly equal in the system                                  */
   double bPumpWasLastOn;
   double pPumpWasLastOn;


   /* some control settings */
   /* Fan aux power is associated with the chiller                              */
   /* pump aux power is associated with the respective coolant stream           */
   /* compressor aux power is also associated with the chiller                  */
   double electronicsAuxPower;
   double currentAuxPower;
   double cumulativeAuxEnergy;

   double sharingTemperatureThreshold;
   double sharingPercent;    /* this is the amount of the battery flow rate */
                             /* that is borrowed by the PCS loop            */
   double sharingEnthalpy;  
   double batteryColdSideTemp;
//   double pcsColdSideTemp;   /* this is ambient temperature */

   /* percent on */           /* coolant flow rate */            /* aux use */                      /* on/off flag */
   double compressorPcnt;                                        /* from cooling18 */               int compressorOnOff;
   double batteryPumpPcnt;    double batVolumeFlowRatePerPcnt;   double batPumpPowerPerPcnt;        int batteryPumpOnOff;
   double inverterPumpPcnt;   double pcsVolumeFlowRatePerPcnt;   double pcsPumpPowerPerPcnt;        int inverterPumpOnOff;
   double fanPcnt;                                               double fanAuxPowerPerPcnt;         int fansOnOff;
   double heaterPcnt;                                            double heaterAuxPower;

   int bTurnedOn;
   int pTurnedOn;
   int imTurnedOn;

   /* two coolant streams are hard-coded in, and enthalpy sharing is allowed */
   /* to occur, which corresponds to the 3-way valve opening between them    */
   struct CoolantStream *batteryStream;
   struct CoolantStream *inverterStream;
   
   struct Chiller *next;

} OChiller, *pChiller;



typedef struct Battery
{
   double mass;
   double cp;
   double k;
   double area;
   double thermalMass;
   double height;
   double dx;
   double temperature[7];
   double tempLast[7];
   double heatIntoColdPlate, hicpLast;
   double heatIntoAir;
   double batteryTemperatureTarget,hysteresis;
   double cumulativeBatteryHeat;
   double roundTripEfficiency;

   double maxBatteryTemp;
   double battAveTempOperating;
   double battAveTempNotOperating;

   double coolantTemp;

   double current;
   double ocv[29][2];    /* open-circuit voltage vs. state of charge */
   double cellHeat[22][6];
   double totalBatteryEnergy;
   double initialSoh;
   double soh;           /* state of heatlth */
   double soc;           /* state of charge  */

   double cellCapacityAh;

   double bottomUA;
   double topUA;

   /* keep track of the average battery temperature during cycling */
   /* and also durin resting, for the SOH fade model               */
   double aveTempWhileResting;
   double aveTempWhileCorD;


   struct Battery *next;   

} OBattery, *pBattery;



typedef struct Inverter
{
   double temperature;
   double tempLast;
   double pcsMass;
   double pcsCp;
   double currentAuxPower;
   double totalAuxEnergy;
   double uaToAir;

   double inverterHeat;
   double heatIntoColdPlate;
   double cumulativeInverterHeat;

   struct Inverter *next;

} OInverter, *pInverter;


typedef struct CoolantStream
{
   double volumeFlowRate;   /* use functions to assign the one and calculate the other flow rate */
   double massFlowRate;
   double coolantVolume;
   double coolantCp;

   double chillerUA;       /* UA is a function of flow rate */
   double coldPlateUA;     /* these numbers are slopws      */ 

   double tlcLast;          /* previous time step value of temp leaving chiller */
   double tecLast;          /* previous time step value of temp entering chiller */

   double tempLeavingChiller;
   double tempEnteringChiller;

   double lastPower;

   struct CoolantStream *next;

} OCoolantStream, *pCoolantStream;


typedef struct Hvac
{
   double airTemp;
   double UA;
   double temperatureTarget;
   double hysteresis;
   double currentAuxPower;
   double coolingPower;

   double totalAuxEnergy;

   /* don't run if the chiller is on */

   struct Hvac *next;

} OHvac, *pHvac;



typedef struct Dehumidifier
{
   double currentAuxPower;
   double totalAuxEnergy;
   double cumulativeDehumidifierOnTime;



   int    isChillerOn;   /* don't run if the chiller is on */

   struct Dehumidifier *next;

} ODehumidifier, *pDehumidifier;



typedef struct AuxLoad
{
   double currentAuxPower;
   double totalAuxEnergy;

   struct AuxLoad *next;
} OAuxLoad, *pAuxLoad;



typedef struct TimeHistory
{
   double time;
   double value;

   struct TimeHistory *next;
} OTimeHistory, *pTimeHistory;



typedef struct ThermalWall
{
   double temp[7];
   double tempLast[7];
   double R[3];
   double area;
   double density;
   double mass;
   double conductivity;
   double cp;
   double totalThickness;

   double innerUA;
   double outerUA;

   double dx;

   struct ThermalWall *next;
} OThermalWall, *pThermalWall;



