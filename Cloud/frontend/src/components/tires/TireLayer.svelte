<script lang="ts">
    import { setContext, getContext } from 'svelte';
    import type { Snippet } from 'svelte';

    interface Props {
        colour: string;
        outer?: boolean;
        scale?: number;
        radius?: number;
        children?: Snippet;
    }

    let { 
        colour, 
        outer = false, 
        scale = 0.75, 
        radius = 24, 
        children 
    }: Props = $props();

    // 1. Get the parent context as a function (if it exists)
    const getParentRadius = getContext<(() => number) | undefined>('tyre-radius');
    
    // 2. Safely evaluate it using a derived rune so it updates reactively
    let parentRadius = $derived(getParentRadius ? getParentRadius() : undefined);
    let isNested = $derived(parentRadius !== undefined);

    // 3. The Magic Fix: Wrap the calculation in $derived() 
    // Now Svelte knows to recalculate this if scale or radius ever change!
    let currentRadius = $derived(isNested ? (parentRadius as number) * scale : radius);

    // 4. Set the context using an arrow function so the child always reads the latest value
    setContext('tyre-radius', () => currentRadius);
</script>

<div 
    class="flex justify-center items-center transition-colors duration-200 overflow-hidden box-border {outer ? 'aspect-[2/3] w-full h-full border-4 border-solid border-black' : ''}"
    style="
        background-color: {colour}; 
        border-radius: {currentRadius}px;
        width: {isNested ? scale * 100 + '%' : '100%'};
        height: {isNested ? scale * 100 + '%' : '100%'};
    "
>
    {@render children?.()}
</div>