<script lang="ts">
    import Tire from './Tire.svelte';

    // Allow the developer to specify the layout style
    // 'horizontal' = I T   T I
    // 'vertical'   = I I over T T
    interface Props {
        layout?: 'horizontal' | 'vertical';
        layerCount?: number;
    }

    let { layout = 'horizontal', layerCount = 3 }: Props = $props();
</script>

<div class="grid grid-cols-2 gap-x-12 gap-y-16 p-8 max-w-4xl mx-auto bg-gray-950 rounded-xl shadow-2xl">

    {#if layout === 'horizontal'}
        <Tire statsPosition="left" {layerCount} />
        <Tire statsPosition="right" {layerCount} />

        <Tire statsPosition="left" {layerCount} />
        <Tire statsPosition="right" {layerCount} />

    {:else if layout === 'vertical'}
        <Tire statsPosition="top" {layerCount} />
        <Tire statsPosition="top" {layerCount} />

        <Tire statsPosition="bottom" {layerCount} />
        <Tire statsPosition="bottom" {layerCount} />
    {/if}

</div>