// found in the _themes/m21/static folder

document.addEventListener('DOMContentLoaded', function() {
	/* Add a [>>>] button on the top-right corner of code samples to hide
	 * the >>> and ... prompts and the output and thus make the code
	 * copyable. */
	var div = document.querySelectorAll('.highlight-python .highlight,' +
			'.highlight-python3 .highlight,' +
			'.highlight-default .highlight');

	// NOTE: in the old jQuery version, `pre` was a jQuery collection across all divs.
	// Here we take the first <pre> we find (if any) to read theme styles.
	var firstPre = null;
	for (var i = 0; i < div.length; i++) {
		var maybePre = div[i].querySelector('pre');
		if (maybePre) {
			firstPre = maybePre;
			break;
		}
	}

	// get the styles from the current theme
	if (firstPre && firstPre.parentElement && firstPre.parentElement.parentElement) {
		firstPre.parentElement.parentElement.style.position = 'relative';
	}
	var hide_text = 'Hide the prompts and output';
	var show_text = 'Show the prompts and output';

	var border_width = '';
	var border_style = '';
	var border_color = '';
	if (firstPre) {
		var cs = window.getComputedStyle(firstPre);
		border_width = cs.borderTopWidth;
		border_style = cs.borderTopStyle;
		border_color = cs.borderTopColor;
	}

	var button_styles = {
		'cursor':'pointer', 'position': 'absolute', 'top': '0', 'right': '0',
		'border-color': border_color, 'border-style': border_style,
		'border-width': border_width, 'color': border_color, 'text-size': '75%',
		'font-family': 'monospace', 'padding-left': '0.2em', 'padding-right': '0.2em',
		'border-radius': '0 3px 0 0'
	};

	function apply_button_styles(button) {
		// Keep the original style keys, but translate the ones that need JS-style names.
		button.style.cursor = button_styles['cursor'];
		button.style.position = button_styles['position'];
		button.style.top = button_styles['top'];
		button.style.right = button_styles['right'];
		button.style.borderColor = button_styles['border-color'];
		button.style.borderStyle = button_styles['border-style'];
		button.style.borderWidth = button_styles['border-width'];
		button.style.color = button_styles['color'];
		// Old code had 'text-size' which is not a real CSS property; map it to font-size.
		button.style.fontSize = '75%';
		button.style.fontFamily = button_styles['font-family'];
		button.style.paddingLeft = button_styles['padding-left'];
		button.style.paddingRight = button_styles['padding-right'];
		button.style.borderRadius = button_styles['border-radius'];
	}

	function hide_elements(parent, selector) {
		var els = parent.querySelectorAll(selector);
		for (var i = 0; i < els.length; i++) {
			els[i].style.display = 'none';
		}
	}

	function show_elements(parent, selector) {
		var els = parent.querySelectorAll(selector);
		for (var i = 0; i < els.length; i++) {
			els[i].style.display = '';
		}
	}

	function set_traceback_visibility(pre, visible) {
		// Equivalent to: button.next('pre').find('.gt').nextUntil('.gp, .go')...
		var gts = pre.querySelectorAll('.gt');
		for (var i = 0; i < gts.length; i++) {
			var n = gts[i].nextSibling;
			while (n) {
				if (n.nodeType === Node.ELEMENT_NODE) {
					var el = n;
					if (el.classList.contains('gp') || el.classList.contains('go')) {
						break;
					}
					el.style.visibility = visible ? 'visible' : 'hidden';
				}
				n = n.nextSibling;
			}
		}
	}

	// create and add the button to all the code blocks that contain >>>
	for (var index = 0; index < div.length; index++) {
		var jthis = div[index];
		var pre = jthis.querySelector('pre');

		// get the styles from the current theme (per-block positioning like before)
		if (pre && pre.parentElement && pre.parentElement.parentElement) {
			pre.parentElement.parentElement.style.position = 'relative';
		}

		if (jthis.querySelectorAll('.gp').length > 0) {
			var button = document.createElement('span');
			button.className = 'copybutton';
			button.textContent = '>>>';
			apply_button_styles(button);
			button.setAttribute('title', hide_text);
			button.setAttribute('data-hidden', 'false');
			jthis.insertBefore(button, jthis.firstChild);
		}

		// tracebacks (.gt) contain bare text elements that need to be
		// wrapped in a span to work with .nextUntil() (see later)
		var preWithGt = jthis.querySelectorAll('pre');
		for (var p = 0; p < preWithGt.length; p++) {
			if (preWithGt[p].querySelector('.gt')) {
				var contents = Array.prototype.slice.call(preWithGt[p].childNodes);
				for (var c = 0; c < contents.length; c++) {
					var node = contents[c];
					if ((node.nodeType === 3) && (node.data.trim().length > 0)) {
						var span = document.createElement('span');
						span.textContent = node.data;
						preWithGt[p].replaceChild(span, node);
					}
				}
			}
		}
	}

	// define the behavior of the button when it's clicked
	var buttons = document.querySelectorAll('.copybutton');
	for (var b = 0; b < buttons.length; b++) {
		buttons[b].addEventListener('click', function(e){
			e.preventDefault();
			var button = this;
			if (button.getAttribute('data-hidden') === 'false') {
				// hide the code output
				hide_elements(button.parentNode, '.go, .gp, .gt');
                var next = button.nextElementSibling;
                while (next && next.tagName.toLowerCase() !== 'pre') {
                    next = next.nextElementSibling;
                }
                if (next) {
                    set_traceback_visibility(next, false);
				}
				button.style.textDecoration = 'line-through';
				button.setAttribute('title', show_text);
				button.setAttribute('data-hidden', 'true');
			} else {
				// show the code output
				show_elements(button.parentNode, '.go, .gp, .gt');
                var next2 = button.nextElementSibling;
                while (next2 && next2.tagName.toLowerCase() !== 'pre') {
                    next2 = next2.nextElementSibling;
                }
                if (next2) {
                    // next2 is the same thing jQuery would return for .next('pre')
					set_traceback_visibility(next2, true);
				}
				button.style.textDecoration = 'none';
				button.setAttribute('title', hide_text);
				button.setAttribute('data-hidden', 'false');
			}
		});
	}
});
