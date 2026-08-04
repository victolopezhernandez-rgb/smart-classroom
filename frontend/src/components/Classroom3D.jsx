import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import {
  buildRoom,
  buildZoneLights,
  updateLights,
  updatePeople,
} from "../utils/classroom3d-helpers.js";

/**
 * 3D classroom digital twin rendered with Three.js.
 *
 * Props:
 *   classroomState: the full state object from the WebSocket hook.
 *     zones: { zone_A: { light, occupancy, natural_light }, ... }
 *     people: [{ id, x, y, zone }, ...]  (optional, added by VisionAgent)
 */
export function Classroom3D({ classroomState }) {
  const mountRef  = useRef(null);
  const sceneRef  = useRef(null);
  const lightsRef = useRef({});
  const peopleRef = useRef([]);
  const rendererRef = useRef(null);

  // ── Build scene once on mount ─────────────────────────────────────────────
  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);

    const camera = new THREE.PerspectiveCamera(
      60,
      mount.clientWidth / mount.clientHeight,
      0.1,
      100
    );
    camera.position.set(5, 8, 14);
    camera.lookAt(5, 0, 4);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.shadowMap.enabled = true;
    renderer.domElement.style.touchAction = 'none'; // OrbitControls necesita esto para touch
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(5, 0, 4);
    controls.maxPolarAngle = Math.PI / 2.1;
    controls.enableDamping = true;

    buildRoom(scene);

    ["zone_A", "zone_B", "zone_C", "zone_D"].forEach((zone) => {
      lightsRef.current[zone] = buildZoneLights(scene, zone);
    });

    let animId;
    const animate = () => {
      animId = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    sceneRef.current = scene;

    // Handle canvas resize
    const handleResize = () => {
      if (!mount) return;
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      if (mount.contains(renderer.domElement)) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, []);

  // ── Update lights + people when state changes ─────────────────────────────
  useEffect(() => {
    if (!classroomState || !sceneRef.current) return;
    // classroomState.zones has format { zone_A: { light, occupancy, natural_light } }
    updateLights(classroomState.zones, lightsRef.current);
    updatePeople(classroomState.people ?? [], sceneRef.current, peopleRef);
  }, [classroomState]);

  return (
    <div
      ref={mountRef}
      className="canvas-3d"
    />
  );
}
