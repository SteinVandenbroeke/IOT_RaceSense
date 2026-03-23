<script lang="ts">
    interface Props {
        value: number;
        unit: string;
    }

    let { 
        value, 
        unit 
    }: Props = $props();
</script>

<article class="bg-zinc-900 border border-zinc-800 rounded-xl p-5 flex flex-col justify-center shadow-lg w-full h-full min-h-25">
    <div class="flex items-baseline gap-2 mt-auto">
        <data value={value.toString()} class="text-4xl font-black text-white tracking-tighter tabular-nums leading-none">
            {Math.round(value)}
        </data>
        <span class="text-zinc-500 font-mono text-4xl leading-tight">
            {unit}
        </span>
    </div>
</article>