This makes a lot of sense. Moving to a dedicated Uno-to-PC bridge with modular switches makes the system incredibly easy to maintain. If a switch breaks or a cord gets snagged, you just swap out a cheap part rather than a whole computer.

Incorporating a Vertical (Up/Down) signal is a great future-proof move—it allows for shifting gears (virtual shifting), navigating menus, or even controlling "Special Abilities" in a team race.

Here is the Notepad-safe summary of this updated hardware strategy:

Project Concept: Modular Handlebar & PC Integration

The "5-Wire" Handlebar Logic (Up/Down Ready)

By using a slightly larger coiled cord (like an RJ12 with 6 wires) or a 5-core cable, we can support the new vertical signals without changing the hardware later.

The Control Map:

X-Axis: Left / Right switches (Lane changes).

Y-Axis: Up / Down switches (Virtual shifting or Menu navigation).

Pulse: The speed sensor from the roller base.

Common: A single Ground wire shared by all inputs.

Handlebar Switch Options

Instead of building buttons from scratch, we can leverage the massive market of "E-bike" or "Motorcycle" handlebar switches available on Amazon.

Off-the-Shelf: Many cheap 3-button or 5-button handlebar pods are waterproof and designed to clamp directly onto standard 22mm bike bars.

3D Printed: For a custom "pro" feel, a 3D-printed housing can be made to hold 4 silent tactile buttons in a "cross" pattern (Up, Down, Left, Right), secured with a velcro strap.

The Stand-Based PC Setup

This configuration turns any old PC into a dedicated "Sim Station."

The "Brain": An Arduino Uno sits in a small 3D-printed box on the monitor stand. It acts as the "HID" (Human Interface Device) or Serial Bridge.

The Stand: A simple wooden or metal floor stand that holds an old office monitor at eye level.

The Link: The 5-core coiled cord plugs into the stand. Any student can roll their bike up, strap on the switches, and be ready in under 60 seconds.

Future-Proofing: Vertical Signals

Adding "Up" and "Down" to the code opens up several possibilities for the gym class or team training:

Virtual Gears: Use "Up/Down" to change the resistance/speed ratio (simulating a 10-speed bike).

Head-Up Display (HUD): Use the buttons to toggle through different stats (Power vs. Rank vs. Map).

Referee Interaction: Use buttons to "Accept" a challenge or "Vote" on the next track.

Summary Table for Notepad

Component: Interface Recommendation: Arduino Uno (USB-Serial to PC).

Component: Switch Pod Recommendation: Amazon E-bike switches or 3D-printed tactile button pods.

Component: Input Wiring Recommendation: 5-core or 6-core coiled cord (X-axis, Y-axis, Pulse, Ground).

Component: Main PC Recommendation: Surplus school PCs (running the Python "Rider Node").

Updated Wiring Pin-out (Notepad Safe)

Wire 1: Common Ground.

Wire 2: Left Signal.

Wire 3: Right Signal.

Wire 4: Up Signal (Vertical).

Wire 5: Down Signal (Vertical).

Wire 6: Pulse Sensor (Speed).

Would you like me to draft the Arduino "Sketch" (the C++ code) that reads these 5 signals and sends them to the PC over the USB cable?