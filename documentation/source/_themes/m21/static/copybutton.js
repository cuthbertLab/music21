// found in the _themes/m21/static folder
// MSAC: I can't remember where this came from, but in 2026 rewritten
// to use modern JS and no jQuery

/** Add a [>>>] button on the top-right corner of code samples to hide
 * the >>> and ... prompts and the output and thus make the code
 * copyable. */
document.addEventListener('DOMContentLoaded', () => {
    const divs = document.querySelectorAll(
        '.highlight-python .highlight,'
        + '.highlight-python3 .highlight,'
        + '.highlight-default .highlight'
    );

    // We take the first <pre> we find (if any) to read theme styles
    // and apply them to the buttons
    let firstPre = null;
    for (const this_div of divs) {
        const maybePre = this_div.querySelector('pre');
        if (maybePre) {
            firstPre = maybePre;
            break;
        }
    }

    // get the styles from the current theme
    if (firstPre && firstPre.parentElement && firstPre.parentElement.parentElement) {
        firstPre.parentElement.parentElement.style.position = 'relative';
    }
    const hide_text = 'Hide the prompts and output';
    const show_text = 'Show the prompts and output';

    let border_width = '';
    let border_style = '';
    let border_color = '';
    if (firstPre) {
        const cs = window.getComputedStyle(firstPre);
        border_width = cs.borderTopWidth;
        border_style = cs.borderTopStyle;
        border_color = cs.borderTopColor;
    }

    function apply_button_styles(button) {
        button.style.cursor = 'pointer';
        button.style.position = 'absolute';
        button.style.top = '0';
        button.style.right = '0';
        button.style.borderColor = border_color;
        button.style.borderStyle = border_style;
        button.style.borderWidth = border_width;
        button.style.color = border_color;
        button.style.fontSize = '75%';
        button.style.fontFamily = 'monospace';
        button.style.paddingLeft = '0.2em';
        button.style.paddingRight = '0.2em';
        button.style.borderRadius = '0 3px 0 0';
    }

    function hide_elements(parent, selector) {
        const els = parent.querySelectorAll(selector);
        for (const el of els) {
            el.style.display = 'none';
        }
    }

    function show_elements(parent, selector) {
        const els = parent.querySelectorAll(selector);
        for (const el of els) {
            el.style.display = '';
        }
    }

    function set_traceback_visibility(pre, visible) {
        // Equivalent to: button.next('pre').find('.gt').nextUntil('.gp, .go')...
        const gts = pre.querySelectorAll('.gt');
        for (const gt of gts) {
            let n = gt.nextSibling;
            while (n) {
                if (n.nodeType === Node.ELEMENT_NODE) {
                    const el = n;
                    if (el.classList.contains('gp') || el.classList.contains('go')) {
                        break;
                    }
                    el.style.visibility = visible ? 'visible' : 'hidden';
                }
                n = n.nextSibling;
            }
        }
    }

    /**
     * find the next sibling that is a <pre> tag.
     */
    function next_pre_sibling(startEl) {
        let next = startEl.nextElementSibling;
        while (next && next.tagName.toLowerCase() !== 'pre') {
            next = next.nextElementSibling;
        }
        return next;
    }

    // create and add the button to all the code blocks that contain >>>
    for (const this_div of divs) {
        // get the styles from the current theme (per-block positioning like before)
        const pre = this_div.querySelector('pre');
        if (pre && pre.parentElement && pre.parentElement.parentElement) {
            pre.parentElement.parentElement.style.position = 'relative';
        }

        if (this_div.querySelectorAll('.gp').length > 0) {
            const button = document.createElement('span');
            button.className = 'copy_button';
            button.textContent = '>>>';
            button.setAttribute('role', 'button');
            button.setAttribute('tabindex', '0');
            apply_button_styles(button);
            button.setAttribute('title', hide_text);
            button.setAttribute('aria-pressed', 'false');
            this_div.insertBefore(button, this_div.firstChild);
        }

        // tracebacks (.gt) contain bare text elements that need to be
        // wrapped in a span to work with .nextUntil() (see later)
        const preWithGt = this_div.querySelectorAll('pre');
        for (const preNode of preWithGt) {
            if (preNode.querySelector('.gt')) {
                const contents = Array.from(preNode.childNodes);
                for (const node of contents) {
                    if ((node.nodeType === Node.TEXT_NODE) && node.data.trim()) {
                        const span = document.createElement('span');
                        span.textContent = node.data;
                        preNode.replaceChild(span, node);
                    }
                }
            }
        }
    }

    // define the behavior of the button when it's clicked
    const buttons = document.querySelectorAll('.copy_button');
    for (const button of buttons) {
        button.addEventListener('click', e => {
            e.preventDefault();
            const parent = button.parentNode;
            const pre = next_pre_sibling(button);
            if (button.getAttribute('aria-pressed') === 'false') {
                // hide the code output
                hide_elements(parent, '.go, .gp, .gt');
                if (pre) {
                    set_traceback_visibility(pre, false);
                }
                button.style.textDecoration = 'line-through';
                button.setAttribute('title', show_text);
                button.setAttribute('aria-pressed', 'true');
            } else {
                // show the code output
                show_elements(parent, '.go, .gp, .gt');
                if (pre) {
                    // pre is the same thing jQuery would return for .next('pre')
                    set_traceback_visibility(pre, true);
                }
                button.style.textDecoration = 'none';
                button.setAttribute('title', hide_text);
                button.setAttribute('aria-pressed', 'false');
            }
        });
        button.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                button.click();
            }
        });
    }
});
