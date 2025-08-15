import { useRef, useMemo, useEffect, useState } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

// Professional Sharp Blockchain Block
function BlockchainBlock({ position, index, scale = 1, isActive, assemblyProgress }) {
    const meshRef = useRef();
    const edgeRef = useRef();
    const [assembled, setAssembled] = useState(false);

    useFrame((state, delta) => {
        if (!meshRef.current) return;

        const time = state.clock.elapsedTime;
        
        // Assembly animation with sharp rotation
        if (assemblyProgress < 1 && !assembled) {
            const targetPos = new THREE.Vector3(...position);
            const startPos = new THREE.Vector3(
                position[0] + (Math.random() - 0.5) * 60,
                position[1] + (Math.random() - 0.5) * 60,
                position[2] + (Math.random() - 0.5) * 60
            );
            
            meshRef.current.position.lerpVectors(startPos, targetPos, assemblyProgress);
            // Sharp, precise rotation during assembly
            meshRef.current.rotation.x = (1 - assemblyProgress) * Math.PI * 6;
            meshRef.current.rotation.y = (1 - assemblyProgress) * Math.PI * 6;
            meshRef.current.rotation.z = (1 - assemblyProgress) * Math.PI * 3;
            
            if (assemblyProgress > 0.95) {
                setAssembled(true);
            }
        } else {
            // Precise geometric rotation after assembly
            const floatOffset = Math.sin(time * 0.3 + index) * 0.15;
            meshRef.current.position.y = position[1] + floatOffset;
            
            // Sharp, controlled rotation on multiple axes
            meshRef.current.rotation.x += delta * 0.4;
            meshRef.current.rotation.y += delta * 0.6;
            meshRef.current.rotation.z += delta * 0.2;
        }

        // Active block effects with sharp scaling
        const targetScale = isActive ? scale * 1.4 : scale;
        const targetEmissive = isActive ? 1.2 : 0.2;
        
        meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.15);
        if (meshRef.current.material) {
            meshRef.current.material.emissiveIntensity = THREE.MathUtils.lerp(
                meshRef.current.material.emissiveIntensity, 
                targetEmissive, 
                0.1
            );
        }

        // Edge glow effect
        if (edgeRef.current) {
            edgeRef.current.material.opacity = isActive ? 0.8 : 0.3;
            edgeRef.current.rotation.copy(meshRef.current.rotation);
        }
    });

    const colors = ['#00d4ff', '#0099cc', '#006699', '#004466', '#002233'];
    const color = useMemo(() => colors[index % colors.length], [index]);

    return (
        <group>
            {/* Main sharp block */}
            <mesh ref={meshRef} position={position} castShadow receiveShadow>
                <boxGeometry args={[1.4, 1.4, 1.4]} />
                <meshStandardMaterial
                    color={color}
                    metalness={0.95}
                    roughness={0.05}
                    emissive={color}
                    emissiveIntensity={0.2}
                    transparent
                    opacity={0.95}
                />
            </mesh>
            
            {/* Sharp edge wireframe */}
            <mesh ref={edgeRef} position={position}>
                <boxGeometry args={[1.45, 1.45, 1.45]} />
                <meshBasicMaterial
                    color="#00ffff"
                    wireframe
                    transparent
                    opacity={0.3}
                />
            </mesh>
        </group>
    );
}

// Sophisticated Energy Bridge
function EnergyBridge({ startPos, endPos, active }) {
    const bridgeRef = useRef();
    const [pulseNodes] = useState(() => 
        Array.from({ length: 5 }, (_, i) => ({ 
            position: i / 4, 
            phase: i * Math.PI * 0.4 
        }))
    );

    const start = useMemo(() => new THREE.Vector3(...startPos), [startPos]);
    const end = useMemo(() => new THREE.Vector3(...endPos), [endPos]);
    const midPoint = useMemo(() => start.clone().lerp(end, 0.5), [start, end]);

    useFrame((state) => {
        if (!bridgeRef.current || !active) return;
        
        bridgeRef.current.children.forEach((node, i) => {
            if (node) {
                const nodeData = pulseNodes[i];
                const progress = nodeData.position;
                const currentPos = start.clone().lerp(end, progress);
                
                node.position.copy(currentPos);
                
                const pulse = 1 + Math.sin(state.clock.elapsedTime * 4 + nodeData.phase) * 0.4;
                node.scale.setScalar(pulse * 0.3);
                
                node.rotation.x += 0.05;
                node.rotation.y += 0.08;
            }
        });
    });

    if (!active) return null;

    return (
        <group ref={bridgeRef}>
            {pulseNodes.map((node, i) => (
                <mesh key={i}>
                    <dodecahedronGeometry args={[0.15, 0]} />
                    <meshStandardMaterial 
                        color="#00ffaa"
                        emissive="#00ccaa"
                        emissiveIntensity={1.2}
                        metalness={0.9}
                        roughness={0.1}
                        transparent
                        opacity={0.8}
                    />
                </mesh>
            ))}
        </group>
    );
}

// Professional 3D Particle Field
function ParticleField() {
    const pointsRef = useRef();
    const orbsRef = useRef();
    const count = 2500;
    const orbCount = 80;
    
    const { positions, colors } = useMemo(() => {
        const pos = new Float32Array(count * 3);
        const col = new Float32Array(count * 3);
        
        for (let i = 0; i < count; i++) {
            const i3 = i * 3;
            
            // Spherical distribution for depth
            const radius = 60 + Math.random() * 40;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            
            pos[i3] = radius * Math.sin(phi) * Math.cos(theta);
            pos[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            pos[i3 + 2] = radius * Math.cos(phi);
            
            // Professional color gradient
            const intensity = Math.random() * 0.8 + 0.2;
            col[i3] = 0.1 * intensity;
            col[i3 + 1] = 0.8 * intensity;
            col[i3 + 2] = 1.0 * intensity;
        }
        
        return { positions: pos, colors: col };
    }, []);

    // 3D floating orbs
    const orbPositions = useMemo(() => {
        return Array.from({ length: orbCount }, () => ({
            position: [
                (Math.random() - 0.5) * 80,
                (Math.random() - 0.5) * 50,
                (Math.random() - 0.5) * 80
            ],
            speed: Math.random() * 0.5 + 0.2,
            scale: Math.random() * 0.3 + 0.1
        }));
    }, []);

    useFrame((state, delta) => {
        if (pointsRef.current) {
            pointsRef.current.rotation.y += delta * 0.1;
            pointsRef.current.rotation.x += delta * 0.03;
            
            const pulse = 1 + Math.sin(state.clock.elapsedTime * 0.8) * 0.3;
            pointsRef.current.material.size = 1.5 * pulse;
        }

        // Animate 3D orbs
        if (orbsRef.current) {
            orbsRef.current.children.forEach((orb, i) => {
                const orbData = orbPositions[i];
                if (orb && orbData) {
                    orb.rotation.x += delta * orbData.speed;
                    orb.rotation.y += delta * orbData.speed * 1.5;
                    orb.position.y += Math.sin(state.clock.elapsedTime * orbData.speed + i) * 0.02;
                }
            });
        }
    });

    return (
        <>
            <points ref={pointsRef}>
                <bufferGeometry>
                    <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
                    <bufferAttribute attach="attributes-color" count={count} array={colors} itemSize={3} />
                </bufferGeometry>
                <pointsMaterial 
                    size={1.5} 
                    transparent 
                    opacity={0.8} 
                    sizeAttenuation 
                    vertexColors
                    blending={THREE.AdditiveBlending}
                />
            </points>
            
            <group ref={orbsRef}>
                {orbPositions.map((orb, i) => (
                    <mesh key={i} position={orb.position} scale={orb.scale}>
                        <icosahedronGeometry args={[0.8, 1]} />
                        <meshStandardMaterial 
                            color="#00ccff"
                            emissive="#0066cc"
                            emissiveIntensity={0.4}
                            metalness={0.8}
                            roughness={0.2}
                            transparent
                            opacity={0.6}
                        />
                    </mesh>
                ))}
            </group>
        </>
    );
}

// Main Scene Component
function Scene() {
    const { camera } = useThree();
    const [assemblyProgress, setAssemblyProgress] = useState(0);
    const [activeBlockIndex, setActiveBlockIndex] = useState(null);
    const [showConnections, setShowConnections] = useState(false);

    // Generate professional grid layout
    const { blockPositions, connections } = useMemo(() => {
        const positions = [];
        const gridSize = 5;
        const spacing = 8;

        // Create 3D grid of blocks
        for (let x = -gridSize; x <= gridSize; x += 2) {
            for (let y = -gridSize; y <= gridSize; y += 2) {
                for (let z = -gridSize; z <= gridSize; z += 2) {
                    if (Math.abs(x) + Math.abs(y) + Math.abs(z) <= gridSize * 1.5) {
                        positions.push([x * spacing, y * spacing, z * spacing]);
                    }
                }
            }
        }

        // Create connections between nearby blocks
        const conns = [];
        for (let i = 0; i < positions.length; i++) {
            for (let j = i + 1; j < positions.length; j++) {
                const p1 = new THREE.Vector3(...positions[i]);
                const p2 = new THREE.Vector3(...positions[j]);
                const dist = p1.distanceTo(p2);

                if (dist < spacing * 2.5 && Math.random() > 0.7) {
                    conns.push({ 
                        startIdx: i, 
                        endIdx: j, 
                        start: positions[i], 
                        end: positions[j] 
                    });
                }
            }
        }

        return { blockPositions: positions, connections: conns };
    }, []);

    // Assembly animation sequence
    useEffect(() => {
        const assemblyTimer = setInterval(() => {
            setAssemblyProgress(prev => {
                if (prev >= 1) {
                    setShowConnections(true);
                    clearInterval(assemblyTimer);
                    return 1;
                }
                return prev + 0.02;
            });
        }, 50);

        return () => clearInterval(assemblyTimer);
    }, []);

    // Active block cycling
    useEffect(() => {
        if (assemblyProgress >= 1) {
            const interval = setInterval(() => {
                setActiveBlockIndex(Math.floor(Math.random() * blockPositions.length));
            }, 2000);
            return () => clearInterval(interval);
        }
    }, [assemblyProgress, blockPositions.length]);

    // Camera setup
    useEffect(() => {
        camera.position.set(0, 15, 35);
        camera.lookAt(0, 0, 0);
    }, [camera]);

    return (
        <>
            {/* Professional cinematic lighting */}
            <ambientLight intensity={0.15} color="#001122" />
            <directionalLight 
                position={[15, 15, 8]} 
                intensity={0.8} 
                color="#ffffff"
                castShadow
                shadow-mapSize-width={4096}
                shadow-mapSize-height={4096}
                shadow-camera-near={0.1}
                shadow-camera-far={100}
                shadow-camera-left={-50}
                shadow-camera-right={50}
                shadow-camera-top={50}
                shadow-camera-bottom={-50}
            />
            <pointLight position={[0, 25, 0]} intensity={0.6} color="#00d4ff" distance={80} />
            <pointLight position={[-25, 0, 25]} intensity={0.4} color="#0099cc" distance={60} />
            <pointLight position={[25, -10, -25]} intensity={0.3} color="#004466" distance={50} />
            <spotLight 
                position={[0, 30, 0]} 
                target-position={[0, 0, 0]}
                intensity={0.5} 
                color="#00ffff"
                angle={Math.PI / 4}
                penumbra={0.5}
                distance={100}
            />

            {/* Professional 3D particle field */}
            <ParticleField />

            {/* Blockchain blocks */}
            {blockPositions.map((position, i) => (
                <BlockchainBlock
                    key={i}
                    position={position}
                    index={i}
                    scale={1}
                    isActive={i === activeBlockIndex}
                    assemblyProgress={assemblyProgress}
                />
            ))}

            {/* Energy bridges */}
            {showConnections && connections.map((connection, i) => (
                <EnergyBridge
                    key={i}
                    startPos={connection.start}
                    endPos={connection.end}
                    active={connection.startIdx === activeBlockIndex || connection.endIdx === activeBlockIndex}
                />
            ))}

            {/* Interactive controls */}
            <OrbitControls 
                autoRotate={assemblyProgress >= 1} 
                autoRotateSpeed={0.5}
                maxDistance={80} 
                minDistance={20} 
                enablePan={false}
                enableDamping
                dampingFactor={0.05}
            />
        </>
    );
}

// Main Component Export
export default function ThreeScene({ className = "" }) {
    const [isLoading, setIsLoading] = useState(true);
    
    useEffect(() => {
        const timer = setTimeout(() => setIsLoading(false), 800);
        return () => clearTimeout(timer);
    }, []);

    if (isLoading) {
        return (
            <div className={`w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-900 to-black ${className}`}>
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-cyan-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-cyan-400 font-medium">Initializing Blockchain Network...</p>
                </div>
            </div>
        );
    }
    
    return (
        <div className={`w-full h-full ${className}`}>
            <Canvas
                shadows
                camera={{ position: [0, 15, 35], fov: 65 }}
                style={{ background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)' }}
                dpr={[1, 2]}
            >
                <Scene />
            </Canvas>
        </div>
    );
}