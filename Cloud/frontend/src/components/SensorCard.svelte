<script lang="ts">
	interface Props {
		title: string;
		value: number | string;
		unit: string;
		status?: 'normal' | 'warning' | 'critical';
	}

	let { title, value, unit, status = 'normal' }: Props = $props();

	let statusColor = $derived(
		status === 'critical' ? 'text-red-500' :
		status === 'warning' ? 'text-amber-500' :
		'text-emerald-400'
	);
	
	let borderColor = $derived(
		status === 'critical' ? 'border-red-500/50' :
		status === 'warning' ? 'border-amber-500/50' :
		'border-zinc-800'
	);
</script>

<article class="bg-zinc-900 border {borderColor} rounded-xl p-5 flex flex-col shadow-lg transition-colors duration-300">
	<dl class="flex flex-col h-full m-0">
		<dt class="text-zinc-400 text-xs font-bold uppercase tracking-widest mb-1">{title}</dt>
		
		<dd class="mt-auto flex items-baseline gap-2 m-0">
			<data value={value.toString()} class="text-4xl font-black {statusColor} tracking-tighter tabular-nums">
				{value}
			</data>
			<span class="text-zinc-500 font-mono text-sm" aria-label="Unit: {unit}">{unit}</span>
		</dd>
	</dl>
</article>