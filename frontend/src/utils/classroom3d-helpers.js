import * as THREE from "three";

// Classroom dimensions: 10m wide × 8m deep × 3m tall
const ROOM = { width: 10, depth: 8, height: 3 };

const ZONE_COLORS = {
  zone_A: 0x4a90d9,
  zone_B: 0x5cb85c,
  zone_C: 0xe8a838,
  zone_D: 0x9b59b6,
};

// Two fixture positions [x, z] per zone
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

  // Zone overlay quads (semi-transparent) on floor
  const zoneCenters = {
    zone_A: [2.5, 2],
    zone_B: [7.5, 2],
    zone_C: [2.5, 6],
    zone_D: [7.5, 6],
  };
  Object.entries(zoneCenters).forEach(([zone, [x, z]]) => {
    const mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(5, 4),
      new THREE.MeshBasicMaterial({
        color: ZONE_COLORS[zone],
        transparent: true,
        opacity: 0.15,
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

  // Walls [x, y, z, rotationY]
  const wallMat = new THREE.MeshLambertMaterial({ color: 0xe8e0d5 });
  [
    [5, 1.5, 0, 0],
    [5, 1.5, 8, Math.PI],
    [0, 1.5, 4, Math.PI / 2],
    [10, 1.5, 4, -Math.PI / 2],
  ].forEach(([x, y, z, ry]) => {
    const wall = new THREE.Mesh(
      new THREE.PlaneGeometry(ROOM.width, ROOM.height),
      wallMat
    );
    wall.position.set(x, y, z);
    wall.rotation.y = ry;
    scene.add(wall);
  });

  // Whiteboard (front wall accent)
  const wbMesh = new THREE.Mesh(
    new THREE.PlaneGeometry(4, 1.2),
    new THREE.MeshLambertMaterial({ color: 0xd6eaf8 })
  );
  wbMesh.position.set(5, 1.8, 0.02);
  scene.add(wbMesh);

  // Desks — 6 columns × 5 rows
  const deskMat = new THREE.MeshLambertMaterial({ color: 0x8b6914 });
  [1.2, 2.8, 4.4, 5.6, 7.2, 8.8].forEach((x) => {
    [1.0, 2.5, 4.0, 5.5, 7.0].forEach((z) => {
      const desk = new THREE.Mesh(
        new THREE.BoxGeometry(0.7, 0.05, 0.5),
        deskMat
      );
      desk.position.set(x, 0.75, z);
      scene.add(desk);
    });
  });

  // Ambient light (always on, low level)
  scene.add(new THREE.AmbientLight(0x404040, 0.4));
}

export function buildZoneLights(scene, zone) {
  const lights = [];
  FIXTURE_POSITIONS[zone].forEach(([x, z]) => {
    // Visual ceiling fixture
    const fixture = new THREE.Mesh(
      new THREE.CylinderGeometry(0.2, 0.2, 0.1, 8),
      new THREE.MeshBasicMaterial({ color: 0x888888 })
    );
    fixture.position.set(x, ROOM.height - 0.05, z);
    fixture.name = `fixture_${zone}`;
    scene.add(fixture);

    // Point light source (starts OFF)
    const pointLight = new THREE.PointLight(0xfff5e0, 0, 8);
    pointLight.position.set(x, ROOM.height - 0.2, z);
    pointLight.castShadow = true;
    scene.add(pointLight);

    lights.push({ fixture, pointLight });
  });
  return lights;
}

export function updateLights(lightingState, zoneLights) {
  if (!lightingState) return;
  const intensities    = { ON: 1.5, DIM: 0.6, OFF: 0.0 };
  const fixtureColors  = { ON: 0xfff9c4, DIM: 0xffe082, OFF: 0x555555 };

  Object.entries(lightingState).forEach(([zone, data]) => {
    if (!zoneLights[zone]) return;
    // data may come from the ClassroomState format (light) or decision format (state)
    const state = data?.light ?? data?.state ?? "OFF";
    zoneLights[zone].forEach(({ fixture, pointLight }) => {
      pointLight.intensity = intensities[state] ?? 0;
      fixture.material.color.setHex(fixtureColors[state] ?? 0x555555);
    });
  });
}

export function updatePeople(people, scene, peopleRef) {
  peopleRef.current.forEach((mesh) => scene.remove(mesh));
  peopleRef.current = [];

  if (!people?.length) return;

  const zoneColors = {
    zone_A: 0x4a90d9,
    zone_B: 0x5cb85c,
    zone_C: 0xe8a838,
    zone_D: 0x9b59b6,
  };

  people.forEach((person) => {
    const color = zoneColors[person.zone] ?? 0xffffff;
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(0.2, 8, 8),
      new THREE.MeshLambertMaterial({ color })
    );
    mesh.position.set(person.x ?? 5, 1.0, person.y ?? 4);
    scene.add(mesh);
    peopleRef.current.push(mesh);
  });
}
