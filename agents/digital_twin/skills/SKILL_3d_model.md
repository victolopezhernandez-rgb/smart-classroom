# SKILL: 3D Classroom Model

## What This Skill Does

Builds the interactive 3D visualization of the classroom using **Three.js** inside a React component. This is the centerpiece of the STEAM fair demo — visitors will see the classroom light up and dim in real time as the AI makes decisions.

## What the 3D Scene Contains

```
Ceiling (flat plane, light gray)
  └── 8 light fixtures (cylinders) — glow yellow when ON, gray when OFF
  
Walls (4 box meshes, beige)
  └── Left wall has 3 window cutouts (transparent blue)

Floor (flat plane, cream color)
  └── Zone overlay grid (4 colored quads, semi-transparent)
      └── Zone A: blue tint | Zone B: green | Zone C: orange | Zone D: purple

Desks (small brown boxes, 30 total arranged in 6×5 grid)

People (small colored spheres, positioned by VisionAgent data)
  └── Color matches their zone

Natural light beam (transparent white quad from windows, opacity = light level)
```

## React Component Structure

```jsx
// frontend/src/components/Classroom3D.jsx

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

/**
 * 3D classroom digital twin rendered with Three.js.
 * 
 * Props:
 *   classroomState: {
 *     lighting: { zone_A: {state: "ON"}, zone_B: {state: "OFF"}, ... }
 *     people: [{id, x, y, zone}, ...]
 *     natural_light: { zone_A: 0.82, ... }
 *   }
 */
export function Classroom3D({ classroomState }) {
  const mountRef = useRef(null);
  const sceneRef  = useRef(null);
  const lightsRef = useRef({});   // Three.js light objects per zone
  const peopleRef = useRef([]);   // Three.js sphere meshes for people

  useEffect(() => {
    // ── 1. Scene Setup ──────────────────────────────────────────────
    const scene    = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);

    const camera = new THREE.PerspectiveCamera(60, mountRef.current.clientWidth / mountRef.current.clientHeight, 0.1, 100);
    camera.position.set(5, 8, 12);
    camera.lookAt(5, 0, 4);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.shadowMap.enabled = true;
    mountRef.current.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(5, 0, 4);
    controls.maxPolarAngle = Math.PI / 2;   // Don't let camera go below floor

    // ── 2. Static Room Geometry ──────────────────────────────────────
    buildRoom(scene);

    // ── 3. Light Fixtures (one PointLight per fixture) ───────────────
    const zones = ["zone_A", "zone_B", "zone_C", "zone_D"];
    zones.forEach(zone => {
      lightsRef.current[zone] = buildZoneLights(scene, zone);
    });

    // ── 4. Animation Loop ────────────────────────────────────────────
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    sceneRef.current = scene;

    // Cleanup on unmount
    return () => {
      renderer.dispose();
      mountRef.current?.removeChild(renderer.domElement);
    };
  }, []);

  // ── Update when classroomState changes ──────────────────────────────
  useEffect(() => {
    if (!classroomState || !sceneRef.current) return;
    updateLights(classroomState.lighting, lightsRef.current);
    updatePeople(classroomState.people, sceneRef.current, peopleRef);
  }, [classroomState]);

  return <div ref={mountRef} style={{ width: "100%", height: "500px" }} />;
}
```

## Helper Functions

```javascript
// frontend/src/utils/classroom3d-helpers.js

import * as THREE from "three";

// Classroom dimensions: 10m wide × 8m deep × 3m tall
const ROOM = { width: 10, depth: 8, height: 3 };

// Zone colors for the floor overlay
const ZONE_COLORS = {
  zone_A: 0x4a90d9,   // Blue
  zone_B: 0x5cb85c,   // Green
  zone_C: 0xe8a838,   // Orange
  zone_D: 0x9b59b6,   // Purple
};

// Light fixture positions per zone [x, z] (y = ceiling height)
const FIXTURE_POSITIONS = {
  zone_A: [[1.5, 1.5], [3.5, 2.5]],
  zone_B: [[6.5, 1.5], [8.5, 2.5]],
  zone_C: [[1.5, 5.5], [3.5, 6.5]],
  zone_D: [[6.5, 5.5], [8.5, 6.5]],
};

export function buildRoom(scene) {
  // Floor
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(ROOM.width, ROOM.depth),
    new THREE.MeshLambertMaterial({ color: 0xf5f0e8 })
  );
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(5, 0, 4);
  floor.receiveShadow = true;
  scene.add(floor);

  // Zone overlays (semi-transparent colored quads on the floor)
  const zoneGeometry = new THREE.PlaneGeometry(5, 4);
  const zoneCenters = {
    zone_A: [2.5, 2], zone_B: [7.5, 2],
    zone_C: [2.5, 6], zone_D: [7.5, 6],
  };
  Object.entries(zoneCenters).forEach(([zone, [x, z]]) => {
    const mesh = new THREE.Mesh(
      zoneGeometry,
      new THREE.MeshBasicMaterial({
        color: ZONE_COLORS[zone], transparent: true, opacity: 0.15
      })
    );
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(x, 0.01, z);
    mesh.name = `zone_overlay_${zone}`;
    scene.add(mesh);
  });

  // Ceiling
  const ceiling = new THREE.Mesh(
    new THREE.PlaneGeometry(ROOM.width, ROOM.depth),
    new THREE.MeshLambertMaterial({ color: 0xffffff, side: THREE.BackSide })
  );
  ceiling.rotation.x = Math.PI / 2;
  ceiling.position.set(5, ROOM.height, 4);
  scene.add(ceiling);

  // Walls (simplified — 4 planes)
  const wallMat = new THREE.MeshLambertMaterial({ color: 0xe8e0d5 });
  [[5, 1.5, 0, 0], [5, 1.5, 8, Math.PI], [0, 1.5, 4, Math.PI/2], [10, 1.5, 4, -Math.PI/2]].forEach(([x, y, z, ry]) => {
    const wall = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.width, ROOM.height), wallMat);
    wall.position.set(x, y, z);
    wall.rotation.y = ry;
    scene.add(wall);
  });

  // Desks (6 columns × 5 rows)
  const deskMat = new THREE.MeshLambertMaterial({ color: 0x8b6914 });
  [1.2, 2.8, 4.4, 5.6, 7.2, 8.8].forEach(x => {
    [1.0, 2.5, 4.0, 5.5, 7.0].forEach(z => {
      const desk = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.05, 0.5), deskMat);
      desk.position.set(x, 0.75, z);
      scene.add(desk);
    });
  });

  // Ambient light (always on, dim)
  scene.add(new THREE.AmbientLight(0x404040, 0.3));
}

export function buildZoneLights(scene, zone) {
  const lights = [];
  FIXTURE_POSITIONS[zone].forEach(([x, z]) => {
    // Visual fixture (cylinder on ceiling)
    const fixture = new THREE.Mesh(
      new THREE.CylinderGeometry(0.2, 0.2, 0.1, 8),
      new THREE.MeshBasicMaterial({ color: 0x888888 })
    );
    fixture.position.set(x, ROOM.height - 0.05, z);
    fixture.name = `fixture_${zone}`;
    scene.add(fixture);

    // Actual light source
    const pointLight = new THREE.PointLight(0xfff5e0, 0, 8);   // intensity=0 (off)
    pointLight.position.set(x, ROOM.height - 0.2, z);
    pointLight.castShadow = true;
    scene.add(pointLight);

    lights.push({ fixture, pointLight });
  });
  return lights;
}

export function updateLights(lightingState, zoneLights) {
  const intensities = { ON: 1.5, DIM: 0.6, OFF: 0.0 };
  const fixtureColors = { ON: 0xfff9c4, DIM: 0xffe082, OFF: 0x555555 };

  Object.entries(lightingState).forEach(([zone, data]) => {
    if (!zoneLights[zone]) return;
    const state = data?.state || "OFF";
    zoneLights[zone].forEach(({ fixture, pointLight }) => {
      pointLight.intensity = intensities[state] ?? 0;
      fixture.material.color.setHex(fixtureColors[state] ?? 0x555555);
    });
  });
}

export function updatePeople(people, scene, peopleRef) {
  // Remove old person meshes
  peopleRef.current.forEach(mesh => scene.remove(mesh));
  peopleRef.current = [];

  if (!people?.length) return;

  const zoneColors = {
    zone_A: 0x4a90d9, zone_B: 0x5cb85c, zone_C: 0xe8a838, zone_D: 0x9b59b6
  };

  people.forEach(person => {
    const color = zoneColors[person.zone] || 0xffffff;
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(0.2, 8, 8),
      new THREE.MeshLambertMaterial({ color })
    );
    // person.x, person.y → Three.js x, z (y is up in Three.js)
    mesh.position.set(person.x, 1.0, person.y);
    scene.add(mesh);
    peopleRef.current.push(mesh);
  });
}
```

## Step-by-Step Build Instructions for Claude Code

1. **Install** Three.js: `npm install three` in the `frontend/` directory
2. **Create** `frontend/src/components/Classroom3D.jsx` with the component above
3. **Create** `frontend/src/utils/classroom3d-helpers.js` with the helper functions
4. **Import** `Classroom3D` in `frontend/src/App.jsx` and render it
5. **Pass** `classroomState` from the WebSocket hook into `Classroom3D`
6. **Test**: you should see a 3D room with 4 colored zones and 30 desks
7. **Verify**: after the WebSocket connects, lights should animate on/off when the AI decides
