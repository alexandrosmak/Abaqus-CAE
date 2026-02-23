      SUBROUTINE VUSDFLD(
     *     NBLOCK, NSTATEV, NFIELDV, NPROPS, NDIR, NSHR,
     *     JELEM, KINTPT, KLAYER, KSECTPT,
     *     STEPTIME, TOTALTIME, DT, CMNAME,
     *     COORDMP, DIRECT, T, CHARLENGTH, PROPS,
     *     STATEOLD, STATENEW, FIELD)

C     === Bring Abaqus parameters FIRST (defines MAXBLK, etc.) ===
      INCLUDE 'VABA_PARAM.INC'

C     === Arguments ===
      INTEGER NBLOCK, NSTATEV, NFIELDV, NPROPS, NDIR, NSHR
      INTEGER JELEM(NBLOCK), KINTPT(NBLOCK), KLAYER(NBLOCK), KSECTPT(NBLOCK)
      CHARACTER*80 CMNAME
      DOUBLE PRECISION STEPTIME, TOTALTIME, DT
      DOUBLE PRECISION COORDMP(NBLOCK,*), DIRECT(NBLOCK,3,3), T(NBLOCK,3,3)
      DOUBLE PRECISION CHARLENGTH(NBLOCK), PROPS(NPROPS)
      DOUBLE PRECISION STATEOLD(NBLOCK,NSTATEV), STATENEW(NBLOCK,NSTATEV)
      DOUBLE PRECISION FIELD(NBLOCK,NFIELDV)

C     === Compile-time constants (MUST precede arrays using them) ===
      INTEGER           NRDATA_PEEQ
      PARAMETER        (NRDATA_PEEQ = 1)

C     === Work arrays sized with MAXBLK*NRDATA_PEEQ ===
      INTEGER           JDATA_PEEQ(MAXBLK*NRDATA_PEEQ)
      CHARACTER*3       CDATA_PEEQ(MAXBLK*NRDATA_PEEQ)
      DOUBLE PRECISION  RDATA_PEEQ (MAXBLK*NRDATA_PEEQ)
      DOUBLE PRECISION  RDATA_PEEQR(MAXBLK*NRDATA_PEEQ)

C     === Other locals ===
      INTEGER           JSTATUS_PEEQ, JSTATUS_PEEQR
      DOUBLE PRECISION  PEEQ_VAL, PEEQR_VAL
      INTEGER           K, IDX

C     ----------------------------------------------------------------
C     Map each block entry to one request slot for VGETVRM
C     (Here we just use the element number; CDATA can be blank.)
C     ----------------------------------------------------------------
      DO K = 1, NBLOCK
         IDX = (K-1)*NRDATA_PEEQ + 1
         JDATA_PEEQ(IDX) = JELEM(K)
         CDATA_PEEQ(IDX) = '   '
      END DO

C     ----------------------------------------------------------------
C     Get plastic strain rate (PEEQR) and cumulative plastic strain (PEEQ)
C     into SEPARATE buffers so we don't overwrite data
C     ----------------------------------------------------------------
      CALL VGETVRM('PEEQR', RDATA_PEEQR, JDATA_PEEQ, CDATA_PEEQ, JSTATUS_PEEQR)
      IF (JSTATUS_PEEQR .NE. 0) THEN
         CALL XPLB_ABQERR(-2, 'VGETVRM PEEQR failed', 0, 0.0D0, ' ')
         CALL XPLB_EXIT
      END IF

      CALL VGETVRM('PEEQ',  RDATA_PEEQ , JDATA_PEEQ, CDATA_PEEQ, JSTATUS_PEEQ)
      IF (JSTATUS_PEEQ .NE. 0) THEN
         CALL XPLB_ABQERR(-2, 'VGETVRM PEEQ failed', 0, 0.0D0, ' ')
         CALL XPLB_EXIT
      END IF

C     ----------------------------------------------------------------
C     Write to STATEV and/or FIELD if available
C     STATEV(1) = PEEQ, STATEV(2) = PEEQR (if at least 2 state vars)
C     FIELD (1) = PEEQ, FIELD (2) = PEEQR (if at least 2 field vars)
C     ----------------------------------------------------------------
      DO K = 1, NBLOCK
         IDX       = (K-1)*NRDATA_PEEQ + 1
         PEEQ_VAL  = RDATA_PEEQ (IDX)
         PEEQR_VAL = RDATA_PEEQR(IDX)

         IF (NSTATEV .GE. 1) STATENEW(K,1) = PEEQ_VAL
         IF (NSTATEV .GE. 2) STATENEW(K,2) = PEEQR_VAL

         IF (NFIELDV .GE. 1) FIELD(K,1) = PEEQ_VAL
         IF (NFIELDV .GE. 2) FIELD(K,2) = PEEQR_VAL
      END DO

      RETURN
      END
