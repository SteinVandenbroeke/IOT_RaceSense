<script lang="ts">
	import { T } from '@threlte/core';
	import { GLTF } from '@threlte/extras';
	import { DEG2RAD } from 'three/src/math/MathUtils.js';

	interface Props {
		roll: number;   // Side-to-side tilt
		pitch: number;  // Front-to-back tilt
		isDegrees?: boolean; // Toggle if input is degrees vs radians
	}

	let { roll = 0, pitch = 0, isDegrees = true }: Props = $props();

	// Convert to Radians if necessary
	let rX = $derived(isDegrees ? pitch * DEG2RAD : pitch);
	let rZ = $derived(isDegrees ? roll * DEG2RAD : roll);
</script>


<T.Group rotation.z={rZ} rotation.x={rX}>
	<T.Group position.y={0.5}>
		<GLTF url="/models/oracle_red_bull_f1_car_rb19_2023.glb" />
	</T.Group>
</T.Group>

<!--<T.Group rotation.x={rX} rotation.z={rZ}>-->

<!--	<T.Mesh castShadow>-->
<!--		<T.BoxGeometry args={[2, 0.6, 4]} />-->
<!--		<T.MeshStandardMaterial color="#3b82f6" roughness={0.2} metalness={0.5} />-->
<!--	</T.Mesh>-->

<!--	<T.Mesh position={[0, 0.35, 0.5]}>-->
<!--		<T.BoxGeometry args={[1.8, 0.2, 1.5]} />-->
<!--		<T.MeshStandardMaterial color="#000000" opacity={0.5} transparent />-->
<!--	</T.Mesh>-->

<!--</T.Group>-->