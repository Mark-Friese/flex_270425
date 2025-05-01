/* 
 * Custom JavaScript for Flexibility Analysis System Documentation
 */

// MathJax configuration
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

// Add copy functionality to code blocks
document.addEventListener("DOMContentLoaded", function() {
  // Add copy buttons to all code blocks
  const codeBlocks = document.querySelectorAll('pre > code');
  
  codeBlocks.forEach((codeBlock) => {
    // Create copy button
    const button = document.createElement('button');
    button.className = 'md-clipboard md-icon';
    button.title = 'Copy to clipboard';
    button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"></path></svg>';
    
    // Add click event
    button.addEventListener('click', (e) => {
      const textToCopy = codeBlock.textContent;
      navigator.clipboard.writeText(textToCopy).then(() => {
        // Show a success message
        button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M21,7L9,19L3.5,13.5L4.91,12.09L9,16.17L19.59,5.59L21,7Z"></path></svg>';
        
        // Reset after 2 seconds
        setTimeout(() => {
          button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"></path></svg>';
        }, 2000);
      }).catch((error) => {
        console.error('Error copying text: ', error);
      });
    });
    
    // Find the closest pre parent
    const preElement = codeBlock.parentElement;
    
    // Create a wrapper div
    const wrapper = document.createElement('div');
    wrapper.className = 'highlight-wrapper';
    wrapper.style.position = 'relative';
    
    // Replace pre with wrapper and move pre inside wrapper
    preElement.parentNode.insertBefore(wrapper, preElement);
    wrapper.appendChild(preElement);
    
    // Add button to wrapper
    wrapper.appendChild(button);
  });
  
  // Add enhanced command-line behavior
  document.querySelectorAll('.command-line').forEach((commandLine) => {
    const copyButton = document.createElement('span');
    copyButton.className = 'copy-button';
    copyButton.textContent = 'Copy';
    
    copyButton.addEventListener('click', () => {
      // Get command text without the prompt
      const commandText = commandLine.textContent.replace(/^\$\s+/gm, '');
      
      navigator.clipboard.writeText(commandText).then(() => {
        copyButton.textContent = 'Copied!';
        setTimeout(() => {
          copyButton.textContent = 'Copy';
        }, 2000);
      });
    });
    
    commandLine.appendChild(copyButton);
  });
});

// Add responsive table handling
document.addEventListener("DOMContentLoaded", function() {
  const tables = document.querySelectorAll('.md-typeset table');
  
  tables.forEach((table) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'table-wrapper';
    wrapper.style.overflowX = 'auto';
    
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);
  });
});
