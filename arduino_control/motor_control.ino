/*
 * motor_control.ino
 * -----------------
 * Arduino control sketch for a 3-cylinder MRI-compatible
 * pneumatic/hydraulic rotary motor.
 *
 * Operating principle
 * -------------------
 * Three solenoid valves (A, B, C) pressurise the three cylinders in
 * sequence, each offset by 120° of shaft rotation.  Only ONE valve is
 * energised at a time ("A on → B, C off"), giving a clean square-wave
 * commutation.
 *
 * Timing (matches the hand-drawn timing graph)
 * ---------------------------------------------
 *   Full revolution  : 1.5 s
 *   Phase per valve  : 0.5 s  (= 1/3 of cycle)
 *   Sequence         : A → B → C → A → …
 *
 * Non-blocking design
 * -------------------
 * millis() is used instead of delay() so the main loop remains free to
 * read additional inputs (speed potentiometer, direction switch, encoder)
 * without missing a timing event.
 *
 * Hardware wiring
 * ---------------
 *   Digital pin 2  →  Valve A solenoid driver (MOSFET gate / relay coil)
 *   Digital pin 3  →  Valve B solenoid driver
 *   Digital pin 4  →  Valve C solenoid driver
 *
 * Author: Sam Tsang (MRI Actuator Project)
 */

// ---------------------------------------------------------------------------
// Pin definitions
// ---------------------------------------------------------------------------
const int PIN_VALVE_A = 2;
const int PIN_VALVE_B = 3;
const int PIN_VALVE_C = 4;

// ---------------------------------------------------------------------------
// Timing constants
// ---------------------------------------------------------------------------
// Duration each valve stays ON (milliseconds).
// 1500 ms total cycle ÷ 3 phases = 500 ms per phase.
unsigned long PHASE_DURATION_MS = 500UL;

// ---------------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------------
// The motor cycles through three phases: 0 = A on, 1 = B on, 2 = C on.
uint8_t currentPhase = 0;

// Stores the millis() timestamp when the current phase started.
unsigned long phaseStartTime = 0;

// ---------------------------------------------------------------------------
// Helper: activate exactly one valve, de-energise the other two.
// ---------------------------------------------------------------------------
void setValves(bool a, bool b, bool c) {
  digitalWrite(PIN_VALVE_A, a ? HIGH : LOW);
  digitalWrite(PIN_VALVE_B, b ? HIGH : LOW);
  digitalWrite(PIN_VALVE_C, c ? HIGH : LOW);
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------
void setup() {
  // Configure valve pins as outputs and make sure all valves start closed.
  pinMode(PIN_VALVE_A, OUTPUT);
  pinMode(PIN_VALVE_B, OUTPUT);
  pinMode(PIN_VALVE_C, OUTPUT);
  setValves(false, false, false);

  // Optional: serial monitor for debugging the phase transitions.
  Serial.begin(9600);
  Serial.println("MRI Motor Controller — ready.");

  // Start the sequence with Valve A.
  currentPhase   = 0;
  phaseStartTime = millis();
  setValves(true, false, false);   // Phase 0: A on, B & C off
  Serial.println("Phase 0 → Valve A ON");
}

// ---------------------------------------------------------------------------
// Main loop (non-blocking)
// ---------------------------------------------------------------------------
void loop() {
  unsigned long now = millis();

  // Check whether the current phase has completed its 500 ms window.
  if (now - phaseStartTime >= PHASE_DURATION_MS) {
    // Advance to the next phase, wrapping around after phase 2.
    currentPhase = (currentPhase + 1) % 3;
    phaseStartTime = now;            // Reset phase timer.

    // Activate the appropriate valve for the new phase.
    switch (currentPhase) {
      case 0:
        setValves(true, false, false);   // A on, B & C off
        Serial.println("Phase 0 → Valve A ON");
        break;
      case 1:
        setValves(false, true, false);   // B on, A & C off
        Serial.println("Phase 1 → Valve B ON");
        break;
      case 2:
        setValves(false, false, true);   // C on, A & B off
        Serial.println("Phase 2 → Valve C ON");
        break;
    }
  }

  // -------------------------------------------------------------------------
  // FUTURE EXPANSION HOOKS
  // -------------------------------------------------------------------------
  // The loop is free here.  Add your sensor reads, e.g.:
  //
  //   int speedPot = analogRead(A0);
  //   PHASE_DURATION_MS = map(speedPot, 0, 1023, 200, 2000); // 0.2–2 s/phase
  //
  //   bool dirPin = digitalRead(5);  // reverse sequence order for CW/CCW
  // -------------------------------------------------------------------------
}
