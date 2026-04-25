
#include "preprocess.h"
#include "data_structures.h"
#include <stdio.h>


void initialize(struct SimMain *simmain);
void parseInputFile(struct SimMain *simmain);
void housekeeping(struct SimMain *simmain);
void transientSolver(struct SimMain *simmain);


int main(void)
{
   /* initializing sets all NULL or NO_INPUT values */
   struct SimMain A, *simmain;   simmain = &A;   initialize(simmain);


   /* read inputs summarize inputs in a file */
   parseInputFile(simmain);


   /* inputs not already populated are given default vaules */
   housekeeping(simmain);


   /* do the transient solve */
   transientSolver(simmain);


   /* close everything out */
   fclose(LOGFILE);

   return 0;
}

