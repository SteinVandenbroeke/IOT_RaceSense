<script lang="ts">
	interface Props {
		title: string; // e.g., "Front Left"
		temp: number;
		tempStat?: 'cold' | 'normal' | 'hot' | 'critical';
		pressure: number;
		presStat?: 'flat' | 'low' | 'normal' | 'high' | 'extreme';
	}

	let { title, temp: temperature, tempStat: tempStat = 'normal', pressure, presStat: pressureStatus = 'normal' }: Props = $props();

	// Helper function to easily assign colors based on individual metric status
	const getColor = (status: string) => {
		if (status === 'critical' || status === "extreme") return 'text-red-500';
		if (status === 'hot' || status === "high") return 'text-amber-500';
		if (status === 'cold' || status === "flat") return 'text-cyan-500'
		return 'text-emerald-400';
	};
</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-4 flex flex-col shadow-lg transition-colors duration-300">
	<header class="border-b border-zinc-800/50 pb-2 mb-3">
		<h3 class="text-zinc-300 text-xs font-bold uppercase tracking-widest">{title}</h3>
	</header>

	<div class="grid grid-cols-2 gap-4">
		<dl class="flex flex-col m-0">
			<dt class="text-zinc-500 text-[10px] uppercase font-bold tracking-wider mb-1">Temperature</dt>
			<dd class="flex items-baseline gap-1 m-0">
				<data value={temperature.toString()} class="text-2xl font-black {getColor(tempStat)} tracking-tighter tabular-nums">
					{temperature}
				</data>
				<span class="text-zinc-600 font-mono text-xs" aria-label="Celsius">°C</span>
			</dd>
		</dl>

		<dl class="flex flex-col m-0 border-l border-zinc-800/50 pl-4">
			<dt class="text-zinc-500 text-[10px] uppercase font-bold tracking-wider mb-1">Pressure</dt>
			<dd class="flex items-baseline gap-1 m-0">
				<data value={pressure.toString()} class="text-2xl font-black {getColor(pressureStatus)} tracking-tighter tabular-nums">
					{pressure}
				</data>
				<span class="text-zinc-600 font-mono text-xs" aria-label="Bar">bar</span>
			</dd>
		</dl>
	</div>
</article>