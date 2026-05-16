import re
import glob

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Add the chart-dots container if it doesn't exist
    if 'id="chart-dots"' not in html:
        # Find the end of the SVG Chart container
        svg_container_pattern = r'(<div class="absolute inset-0 pb-6">\s*<svg id="chart-svg".*?</svg>\s*</div>)'
        html = re.sub(svg_container_pattern, r'\1\n                    <!-- Dots Overlay -->\n                    <div id="chart-dots" class="absolute inset-0 pb-6 pointer-events-none"></div>', html, flags=re.DOTALL)

    # 2. Add JavaScript logic to grab chartDots
    if 'const chartSvg' in html and 'const chartDots' not in html:
        html = html.replace('const chartSvg = document.getElementById(\'chart-svg\');',
                            'const chartSvg = document.getElementById(\'chart-svg\');\n            const chartDots = document.getElementById(\'chart-dots\');')

    # 3. We need to create weightDots and heightDots
    if 'const weightSvg =' in html and 'const weightDots =' not in html:
        # We will manually replace the <g> block in the SVG with an empty string,
        # and create a new constant for the dots.
        
        weight_dots_html = """
            const weightDots = `
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 0%; top: 99%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 20%; top: 98%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 40%; top: 94%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 60%; top: 81%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 80%; top: 62.5%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-4 h-4 bg-primary rounded-full border-2 border-white shadow-md" style="left: 100%; top: 25%; transform: translate(-50%, -50%);"></div>
            `;
        """
        
        height_dots_html = """
            const heightDots = `
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 0%; top: 99.2%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 20%; top: 95%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 40%; top: 90%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 60%; top: 80%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 80%; top: 58%; transform: translate(-50%, -50%);"></div>
                <div class="absolute w-4 h-4 bg-primary rounded-full border-2 border-white shadow-md" style="left: 100%; top: 45%; transform: translate(-50%, -50%);"></div>
            `;
        """
        
        # Strip out the <g>...</g> containing circles from SVG scripts
        html = re.sub(r'<g>\s*<circle cx="0" cy="99".*?</g>', '', html, flags=re.DOTALL)
        html = re.sub(r'<g>\s*<circle cx="0" cy="99\.2".*?</g>', '', html, flags=re.DOTALL)
        
        # Also remove the static <g> from the main HTML (initial render)
        # We handle this by replacing the SVG <g> entirely and putting the initial HTML dots in the chart-dots div.
        
        # Insert variables
        html = html.replace('const weightSvg =', weight_dots_html + '\n            const weightSvg =')
        html = html.replace('const heightSvg =', height_dots_html + '\n            const heightSvg =')

    # 4. Update the event listeners to swap dots
    if 'chartSvg.innerHTML = heightSvg;' in html and 'chartDots.innerHTML = heightDots;' not in html:
        html = html.replace('chartSvg.innerHTML = heightSvg;', 'chartSvg.innerHTML = heightSvg;\n                if(chartDots) chartDots.innerHTML = heightDots;')
    if 'chartSvg.innerHTML = weightSvg;' in html and 'chartDots.innerHTML = weightDots;' not in html:
        html = html.replace('chartSvg.innerHTML = weightSvg;', 'chartSvg.innerHTML = weightSvg;\n                if(chartDots) chartDots.innerHTML = weightDots;')

    # 5. Fix the initial render in the HTML body
    # Find the initial <div id="chart-dots"...></div> and insert the weight dots
    initial_dots = """<div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 0%; top: 99%; transform: translate(-50%, -50%);"></div>
                        <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 20%; top: 98%; transform: translate(-50%, -50%);"></div>
                        <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 40%; top: 94%; transform: translate(-50%, -50%);"></div>
                        <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 60%; top: 81%; transform: translate(-50%, -50%);"></div>
                        <div class="absolute w-3 h-3 bg-primary rounded-full" style="left: 80%; top: 62.5%; transform: translate(-50%, -50%);"></div>
                        <div class="absolute w-4 h-4 bg-primary rounded-full border-2 border-white shadow-md" style="left: 100%; top: 25%; transform: translate(-50%, -50%);"></div>"""
    
    html = re.sub(r'(<div id="chart-dots" class="absolute inset-0 pb-6 pointer-events-none">)</div>',
                  r'\1\n                        ' + initial_dots + '\n                    </div>', html)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

process_file('index.html')
process_file('home_baby.html')
