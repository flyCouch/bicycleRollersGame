Project Concept: Roller Racer LAN (Modular Edition)

System Architecture

Instead of one script running everything, the system would split into two distinct roles:

The Hub (The "Referee"): A central server computer that handles the "Source of Truth." It calculates the global Z-position and lane of every rider, manages the spawning of obstacles, and generates the behavior of "Random" (NPC) riders.

The Nodes (The "Riders"): Each rider has a dedicated station (PC + Screen + Bike). The Node sends "Pulse" data to the Hub and receives the positions of all other riders to render them locally.

Scaling to 100 Riders

To handle a full gym class or a large cycling team, the software utilizes distributed processing.

Network Protocol: Uses UDP Sockets for movement data. Unlike TCP, UDP doesn't wait for "handshakes," ensuring zero lag for real-time speed updates.

Broadcast Frequency: The Hub sends updates at 60Hz (60 times per second) to match the screen refresh rate.

Hardware Efficiency: Because each Node only renders its own perspective, the graphics load is distributed. 100 screens = 100 GPUs working together.

The "Referee" Dashboard

A dedicated interface for the teacher or coach to control the session:

Global Reset: Synchronized start/stop for all 100 bikes.

Hazard Control: Drop oil slicks or blockades manually to test student reflexes.

NPC Density: Increase/decrease "Randoms" on the fly to change traffic difficulty.

Spectator View: A top-down map showing every rider's position for the big screen in the gym.

Advanced Training Features

Drafting Mechanics: To simulate real-world cycling physics, the system includes a "Slipstream" logic.

The Logic: If Rider A is within 2 meters of Rider B and sharing the same lane, the Hub reduces the "Wind Resistance" constant for Rider A.

The Formula: Speed_final = (Pulses * Sensitivity) * Draft_multiplier

Visual Feedback: The screen border glows blue when a rider successfully enters a draft.

Team Mode & Ghost Riders:

Lead-out Trains: Teams of riders can practice rotating the front position to save energy for a final sprint.

Data Logging: The Hub logs every pulse. Students can race against their "Ghost" (their best performance from a previous week) or a "Professional Pace" set by the coach.

Technical Summary

Component: Communication Function: UDP/IP for low-latency movement updates.

Component: Modular UI Function: Standardized Client software; enter "Station ID" to join the race.

Component: Hardware Function: Raspberry Pi 5 or Mini-PCs at each bike; Central Laptop for Hub.

Component: Data Output Function: Automatic CSV/Excel export for grading and athletic tracking.

Practical Application: A Gym Class Use Case

The Setup: 30-100 bikes are arranged in the gym. Each has a monitor.

The Wake-up: Students begin pedaling; the "Rider Node" connects to the "Referee Hub" automatically.

The Race: The teacher sets a 10km goal. The gym is filled with synthesized harmonies as riders overtake one another.

The Results: At the finish line, the Hub displays a podium. The teacher receives a file containing the Average Wattage/Speed equivalent for every student to track fitness progress over the semester.