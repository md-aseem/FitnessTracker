/*===================================================================*/
/* This routine parses the input file, with # being a comment symbol */
/*===================================================================*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "data_structures.h"
#include "preprocess.h"
//#include "includer.h"

double getValue(FILE *f);
void   getString(FILE *f,char *d);


void parseInputFile(struct SimMain *simmain)
{
   struct Battery *b = batteryListHead;
   char c,buffer[120],loader[2];
   int i,match;
   char const *namelist[IN_ANYmain] = {
      "@FIXED_AMBIENT_TEMPERATURE_C",
      "@INITIAL_BATTERY_TEMPERATURE_C",
      "@MAX_CHARGE_RATE",
      "@MAX_DISCHARGE_RATE",
      "@CHILLER_MODEL",
      "@CHILLER_NOISE_KIT",
      "@BATTERY_MODEL",
      "@HVAC_OPTION_PRESENT",
      "@SUNRISE_TIME",
      "@SUNSET_TIME",
      "@BATTERY_CONDITION",
      "@INITIAL_STATE_OF_CHARGE",
      "@POWER_TIME_HISTORY_FILE"};


   FILE *f = fopen("input.in","r");

   if(f == NULL)
   {
      fprintf(LOGFILE,"   ERROR!  FILE input.in WAS NOT ABLE TO BE OPENED!\n");
      fprintf(LOGFILE,"     THE FILE input.in IS REQUIRED TO GET INPUTS!\n\n");
      fprintf(LOGFILE,"                  *** ABORTING! ***              \n\n");
      exit(1);
   }


   fprintf(LOGFILE,"  ******* READING INPUTS FROM FILE in.input *******\n\n");

   /* Read into a buffer, character-by-character, until you reach a comment or a newline*/
   while((c=getc(f)) != EOF)
   {
      if(c == '#')    /* If there is a comment */
      {
         while((c=getc(f)) != EOF)
         {
            if(c == '#')
            {
               buffer[0] = '\0';
               break;
            }
            else if(c == '\n')
            {
               buffer[0] = '\0';
               break;
            }
         }
      }
//      else if(c == '}')
//      {
//         return ;
//      }
      else
      {
         if( !((c == ' ') || (c == '\n') || (c == '\t'))) /* Ignore whitespace */
         {
            loader[0] = c;  loader[1] = '\0';  if(c != '{') strcat(buffer,loader);
            if(c == '{')
            {
               match = NO;
               fseek(f,-1,SEEK_CUR);
               /* Compare buffer string with the list */
               for(i=1;i<=IN_ANYmain;i++)
               {
                  if(strcmp(buffer,namelist[i-1]) == 0)
                  {
                     switch(i-1)
                     {
                        case FIXED_AMB_TEMP:
                           simmain->ambientTemperature = getValue(f);              match = YES;
                           fprintf(LOGFILE,"\n FIXED AMBIENT TEMPERATURE:          %5.2f (degress C)",simmain->ambientTemperature);
                           simmain->ambientTemperature += 273.15;
                           break;
                        case INITIAL_TEMP:
                           simmain->initialTemperature = getValue(f);              match = YES;
                           fprintf(LOGFILE,"\n COMPONENT INITIAL TEMPERATURE:      %5.2f (degrees C)",simmain->initialTemperature);
                           simmain->initialTemperature += 273.15;
                           simmain->internalAirTemp     = simmain->initialTemperature;
                           simmain->internalAirTempPrev = simmain->initialTemperature;
                           break;
                        case MAX_CHARGE_RATE:
                           simmain->cRate = getValue(f);                           match = YES;
                           fprintf(LOGFILE,"\n MAX CHARGE RATE:                    %4.2f",simmain->cRate);
                           break;
                        case MAX_DISCHARGE_RATE:
                           simmain->dRate = getValue(f);                           match = YES;
                           fprintf(LOGFILE,"\n MAX DISCHARGE RATE:                 %4.2f",simmain->dRate);
                           break;
                        case CHILLER_MODEL:
                           getString(f,simmain->chillerModelName);                 match = YES;
                           fprintf(LOGFILE,"\n CHILLER MODEL:                      %s",simmain->chillerModelName);
                           break;
                        case CHILLER_NOISE_KIT:
                           getString(f,simmain->chillerNoiseKit);                  match = YES;
                           fprintf(LOGFILE,"\n CHILLER NOISE KIT PRESENT:          %s",simmain->chillerNoiseKit);
                           break;
                        case BATTERY_MODEL:
                           getString(f,simmain->batteryModelName);                 match = YES;
                           fprintf(LOGFILE,"\n BATTERY MODEL:                      %s",simmain->batteryModelName);
                           break;
                        case HVAC_OPTION_PRESENT:
//                           getString(f,simmain->batteryModelName);                 match = YES;
//                           fprintf(LOGFILE,"\n BATTERY MODEL:                      %s",simmain->batteryModelName);
                           break;
                        case TIME_OF_SUNRISE:
                           simmain->sunriseTime = getValue(f);                     match = YES;
                           fprintf(LOGFILE,"\n SUN COMES UP:                       %5.2f hours",simmain->sunriseTime);
                           simmain->sunriseTime = simmain->sunriseTime*CONVERT_HOURS_TO_SECONDS;
                           break;
                        case TIME_OF_SUNSET:
                           simmain->sunsetTime = getValue(f);                      match = YES;
                           fprintf(LOGFILE,"\n SUN GOES DOWN:                      %5.2f hours",simmain->sunsetTime);
                           simmain->sunsetTime = simmain->sunsetTime*CONVERT_HOURS_TO_SECONDS;
                           break;
                        case BATTERY_LIFE:
                           getString(f,simmain->batteryLifeStatus);                match = YES;
                           fprintf(LOGFILE,"\n BATTERY LIFE CONDITION:             %s",simmain->batteryLifeStatus);
                           break;
                        case INITIAL_SOC:
                           b->soc = getValue(f);                      match = YES;
                           fprintf(LOGFILE,"\n INITIAL STATE OF CHARGE:            %5.2f PERCENT",b->soc);
                           break;
                        case POWER_FILE_NAME:
                           getString(f,simmain->powerFileName);                    match = YES;
                           fprintf(LOGFILE,"\n POWER vs TIME WILL BE READ FROM:    %s",simmain->powerFileName);
                           break;
                     }
                  }
               }
               if(match == NO)
               {  
                  fprintf(LOGFILE,"\n\n ERROR!  no matching keyword for %s\n",buffer);
                  fprintf(LOGFILE," exiting!\n\n");
                  exit(1);
               }
            }
         }
         else if(c == '\n') /* Reset buffer with each newline */
         {
            buffer[0] = '\0';
         }
      }
   }

   fclose(f);

   fprintf(LOGFILE,"\n\n\n *** FINISHED READING INPUTS ***\n\n");

   /* before leaving the parsing phase, I want to make sure that each  */
   /* thermal connection has in it the temperature of the neighboring  */
   /* compartment or ambient                                           */
   return ;
}
