<script lang="ts">
	import { Canvas, T } from '@threlte/core';
	import { ContactShadows, Float, OrbitControls } from '@threlte/extras';
	import CarModel from './CarModel.svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		roll?: number; // Lateral G (Left/Right)
		pitch?: number; // Longitudinal G (Braking/Acceleration
	}

	let {
		roll = 0,
		pitch = 0
	}: Props = $props();

</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col shadow-lg transition-colors duration-300 relative w-full aspect-square max-w-sm mx-auto">
	<h3 class="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mb-1">Roll and pitch</h3>
	<Canvas>
		<T.PerspectiveCamera makeDefault position={[5, 3, 5]} fov={35}>
			<OrbitControls enableZoom={false} />
		</T.PerspectiveCamera>

		<T.AmbientLight intensity={0.8} />
		<T.DirectionalLight position={[10, 10, 5]} intensity={1} />

		<T.Group>
			<Float floatIntensity={1} speed={2}>
				<T.Group position.y={-0.5} position.x={0.5}>
					<CarModel roll={roll} pitch={pitch}></CarModel>
				</T.Group>
			</Float>
		</T.Group>

		<ContactShadows scale={10} blur={2} far={2.5} opacity={0.5} />
	</Canvas>
</article>