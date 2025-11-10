/**
 * Enhanced Markdown Editor with Live Preview and Obsidian Compatibility
 * Provides real-time markdown preview, toolbar shortcuts, and drag-drop support
 */

class MarkdownEditor {
    constructor(textareaId, options = {}) {
        this.textarea = document.getElementById(textareaId);
        this.options = {
            showPreview: options.showPreview !== false,
            enableToolbar: options.enableToolbar !== false,
            enableDragDrop: options.enableDragDrop !== false,
            previewUpdateDelay: options.previewUpdateDelay || 300,
            ...options
        };
        
        this.isPreviewVisible = false;
        this.updateTimer = null;
        
        this.init();
    }
    
    init() {
        if (!this.textarea) {
            console.error('Textarea not found for MarkdownEditor');
            return;
        }
        
        this.createEditorStructure();
        this.setupToolbar();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        
        if (this.options.enableDragDrop) {
            this.setupDragDrop();
        }
        
        // Initial preview update
        if (this.options.showPreview) {
            this.updatePreview();
        }
    }
    
    createEditorStructure() {
        // Create editor container
        this.editorContainer = document.createElement('div');
        this.editorContainer.className = 'markdown-editor';
        
        // Create toolbar
        this.toolbar = document.createElement('div');
        this.toolbar.className = 'markdown-toolbar';
        
        // Create editor panes container
        this.panesContainer = document.createElement('div');
        this.panesContainer.className = 'markdown-editor-panes';
        
        // Create input pane
        this.inputPane = document.createElement('div');
        this.inputPane.className = 'markdown-input-pane';
        
        // Create preview pane
        this.previewPane = document.createElement('div');
        this.previewPane.className = 'markdown-preview-pane';
        this.previewPane.style.display = 'none'; // Hidden by default
        
        this.preview = document.createElement('div');
        this.preview.className = 'markdown-preview markdown-content';
        this.previewPane.appendChild(this.preview);
        
        // Wrap original textarea
        this.textarea.parentNode.insertBefore(this.editorContainer, this.textarea);
        this.editorContainer.appendChild(this.toolbar);
        this.editorContainer.appendChild(this.panesContainer);
        this.panesContainer.appendChild(this.inputPane);
        this.panesContainer.appendChild(this.previewPane);
        this.inputPane.appendChild(this.textarea);
        
        // Update textarea styling
        this.textarea.className += ' markdown-textarea';
    }
    
    setupToolbar() {
        if (!this.options.enableToolbar) return;
        
        const toolbarButtons = [
            {
                group: 'formatting',
                buttons: [
                    { icon: 'B', title: 'Bold', action: () => this.wrapSelection('**', '**', 'bold text') },
                    { icon: 'I', title: 'Italic', action: () => this.wrapSelection('*', '*', 'italic text') },
                    { icon: '`', title: 'Code', action: () => this.wrapSelection('`', '`', 'code') },
                ]
            },
            {
                group: 'headers',
                buttons: [
                    { icon: 'H1', title: 'Header 1', action: () => this.insertAtLineStart('# ', 'Header 1') },
                    { icon: 'H2', title: 'Header 2', action: () => this.insertAtLineStart('## ', 'Header 2') },
                    { icon: 'H3', title: 'Header 3', action: () => this.insertAtLineStart('### ', 'Header 3') },
                ]
            },
            {
                group: 'lists',
                buttons: [
                    { icon: '•', title: 'Bullet List', action: () => this.insertAtLineStart('- ', 'List item') },
                    { icon: '1.', title: 'Numbered List', action: () => this.insertAtLineStart('1. ', 'List item') },
                    { icon: '☐', title: 'Task List', action: () => this.insertAtLineStart('- [ ] ', 'Task item') },
                ]
            },
            {
                group: 'obsidian',
                buttons: [
                    { icon: '[[]]', title: 'Wiki Link', action: () => this.wrapSelection('[[', ']]', 'Course Title') },
                    { icon: '![[]]', title: 'Image Embed', action: () => this.wrapSelection('![[', ']]', 'image.png') },
                    { icon: '[!]', title: 'Callout', action: () => this.insertCallout() },
                ]
            },
            {
                group: 'tools',
                buttons: [
                    { icon: '🔗', title: 'Link', action: () => this.insertLink() },
                    { icon: '```', title: 'Code Block', action: () => this.insertCodeBlock() },
                    { icon: '👁', title: 'Toggle Preview', action: () => this.togglePreview(), id: 'preview-toggle' },
                ]
            }
        ];
        
        toolbarButtons.forEach(group => {
            const btnGroup = document.createElement('div');
            btnGroup.className = 'btn-group';
            
            group.buttons.forEach(btn => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'btn btn-sm';
                button.innerHTML = btn.icon;
                button.title = btn.title;
                button.onclick = (e) => {
                    e.preventDefault();
                    btn.action();
                };
                
                if (btn.id) {
                    button.id = btn.id;
                }
                
                btnGroup.appendChild(button);
            });
            
            this.toolbar.appendChild(btnGroup);
        });
        
        // Add help button
        const helpBtn = document.createElement('button');
        helpBtn.type = 'button';
        helpBtn.className = 'btn btn-sm';
        helpBtn.innerHTML = '?';
        helpBtn.title = 'Markdown Help';
        helpBtn.onclick = (e) => {
            e.preventDefault();
            this.showHelp();
        };
        this.toolbar.appendChild(helpBtn);
    }
    
    setupEventListeners() {
        // Update preview on input
        this.textarea.addEventListener('input', () => {
            this.schedulePreviewUpdate();
        });
        
        // Handle tab key for indentation
        this.textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                this.insertTab();
            }
        });
        
        // Auto-resize textarea
        this.textarea.addEventListener('input', () => {
            this.autoResize();
        });
        
        // Initial resize
        this.autoResize();
    }
    
    setupKeyboardShortcuts() {
        this.textarea.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + shortcuts
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'b':
                        e.preventDefault();
                        this.wrapSelection('**', '**', 'bold text');
                        break;
                    case 'i':
                        e.preventDefault();
                        this.wrapSelection('*', '*', 'italic text');
                        break;
                    case '`':
                        e.preventDefault();
                        this.wrapSelection('`', '`', 'code');
                        break;
                    case 'k':
                        e.preventDefault();
                        this.insertLink();
                        break;
                    case 'p':
                        e.preventDefault();
                        this.togglePreview();
                        break;
                }
            }
        });
    }
    
    setupDragDrop() {
        const dropZone = this.inputPane;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-hover');
            }, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-hover');
            }, false);
        });
        
        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        }, false);
    }
    
    // Text manipulation methods
    wrapSelection(prefix, suffix, placeholder = '') {
        const start = this.textarea.selectionStart;
        const end = this.textarea.selectionEnd;
        const selectedText = this.textarea.value.substring(start, end);
        const replacement = selectedText || placeholder;
        
        const newText = prefix + replacement + suffix;
        
        this.replaceSelection(newText);
        
        // Set cursor position
        if (!selectedText && placeholder) {
            this.textarea.setSelectionRange(start + prefix.length, start + prefix.length + placeholder.length);
        } else {
            this.textarea.setSelectionRange(start + newText.length, start + newText.length);
        }
        
        this.textarea.focus();
        this.schedulePreviewUpdate();
    }
    
    insertAtLineStart(prefix, placeholder = '') {
        const start = this.textarea.selectionStart;
        const value = this.textarea.value;
        
        // Find the start of the current line
        const lineStart = value.lastIndexOf('\n', start - 1) + 1;
        const lineEnd = value.indexOf('\n', start);
        const currentLine = value.substring(lineStart, lineEnd === -1 ? value.length : lineEnd);
        
        // Check if line already has the prefix
        if (currentLine.startsWith(prefix)) {
            // Remove prefix
            const newLine = currentLine.substring(prefix.length);
            this.textarea.setSelectionRange(lineStart, lineEnd === -1 ? value.length : lineEnd);
            this.replaceSelection(newLine);
        } else {
            // Add prefix
            const newLine = prefix + (currentLine || placeholder);
            this.textarea.setSelectionRange(lineStart, lineEnd === -1 ? value.length : lineEnd);
            this.replaceSelection(newLine);
        }
        
        this.textarea.focus();
        this.schedulePreviewUpdate();
    }
    
    replaceSelection(replacement) {
        const start = this.textarea.selectionStart;
        const end = this.textarea.selectionEnd;
        const value = this.textarea.value;
        
        this.textarea.value = value.substring(0, start) + replacement + value.substring(end);
        this.textarea.setSelectionRange(start + replacement.length, start + replacement.length);
    }
    
    insertTab() {
        this.replaceSelection('    '); // 4 spaces
    }
    
    insertLink() {
        const url = prompt('Enter URL:');
        if (url) {
            const text = this.getSelectedText() || 'link text';
            this.wrapSelection('[', `](${url})`, text);
        }
    }
    
    insertCodeBlock() {
        const language = prompt('Enter language (optional):') || '';
        const placeholder = 'code here';
        this.wrapSelection('```' + language + '\n', '\n```', placeholder);
    }
    
    insertCallout() {
        const types = ['note', 'tip', 'warning', 'danger', 'info', 'success', 'question', 'quote'];
        const type = prompt(`Enter callout type (${types.join(', ')}):`) || 'note';
        const title = prompt('Enter callout title (optional):') || type.charAt(0).toUpperCase() + type.slice(1);
        
        this.replaceSelection(`> [!${type}] ${title}\n> Your callout content here`);
        this.schedulePreviewUpdate();
    }
    
    getSelectedText() {
        return this.textarea.value.substring(this.textarea.selectionStart, this.textarea.selectionEnd);
    }
    
    // Preview methods
    togglePreview() {
        this.isPreviewVisible = !this.isPreviewVisible;
        
        if (this.isPreviewVisible) {
            this.previewPane.style.display = 'block';
            this.updatePreview();
            document.getElementById('preview-toggle').innerHTML = '👁️‍🗨️';
        } else {
            this.previewPane.style.display = 'none';
            document.getElementById('preview-toggle').innerHTML = '👁';
        }
    }
    
    schedulePreviewUpdate() {
        if (!this.isPreviewVisible) return;
        
        clearTimeout(this.updateTimer);
        this.updateTimer = setTimeout(() => {
            this.updatePreview();
        }, this.options.previewUpdateDelay);
    }
    
    async updatePreview() {
        if (!this.isPreviewVisible) return;
        
        const content = this.textarea.value;
        if (!content.trim()) {
            this.preview.innerHTML = '<p class="text-muted">Preview will appear here as you type...</p>';
            return;
        }
        
        try {
            // Simple client-side markdown preview (basic)
            // In a real implementation, you'd send this to the server for proper processing
            const html = this.simpleMarkdownToHtml(content);
            this.preview.innerHTML = html;
        } catch (error) {
            console.error('Preview update error:', error);
            this.preview.innerHTML = '<p class="text-danger">Preview error occurred</p>';
        }
    }
    
    // Simple client-side markdown conversion (basic implementation)
    simpleMarkdownToHtml(markdown) {
        let html = markdown;
        
        // Headers
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
        
        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Code
        html = html.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Wiki Links
        html = html.replace(/\[\[([^\]]+)\]\]/g, '<a href="#" class="wiki-link internal-link">$1</a>');
        
        // Image Embeds
        html = html.replace(/!\[\[([^\]]+)\]\]/g, '<img src="/media/course_materials/$1" class="obsidian-image" alt="$1">');
        
        // Callouts
        html = html.replace(/> \[!(\w+)\] (.*)/g, '<div class="callout callout-$1 alert"><div class="callout-title"><strong>$2</strong></div></div>');
        
        // Lists
        html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Line breaks
        html = html.replace(/\n/g, '<br>');
        
        return html;
    }
    
    // Utility methods
    autoResize() {
        this.textarea.style.height = 'auto';
        this.textarea.style.height = Math.max(200, this.textarea.scrollHeight) + 'px';
    }
    
    handleFileUpload(file) {
        if (file.type.startsWith('image/')) {
            // For images, insert image embed syntax
            const filename = file.name;
            this.replaceSelection(`![[${filename}]]`);
            // Note: In a real implementation, you'd upload the file first
        } else {
            // For other files, insert a link
            const filename = file.name;
            this.replaceSelection(`[${filename}](${filename})`);
        }
        this.schedulePreviewUpdate();
    }
    
    showHelp() {
        const helpContent = `
            <div class="markdown-help">
                <h5>Enhanced Markdown Help</h5>
                <div class="row">
                    <div class="col-md-6">
                        <h6>Basic Formatting:</h6>
                        <code>**bold** *italic* \`code\`</code><br>
                        <code># Header 1</code><br>
                        <code>## Header 2</code><br>
                        <code>- List item</code><br>
                        <code>1. Numbered list</code><br>
                        <code>- [ ] Task item</code>
                    </div>
                    <div class="col-md-6">
                        <h6>Obsidian Features:</h6>
                        <code>[[Course Title]]</code> - Link to course<br>
                        <code>![[image.png]]</code> - Embed image<br>
                        <code>> [!note] Title</code> - Callout box<br>
                        <code>\`\`\`python<br>code here<br>\`\`\`</code> - Code block
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <h6>Keyboard Shortcuts:</h6>
                        <code>Ctrl+B</code> Bold, <code>Ctrl+I</code> Italic, <code>Ctrl+K</code> Link, <code>Ctrl+P</code> Toggle Preview
                    </div>
                </div>
            </div>
        `;
        
        // Simple alert for now (in real app, could use a modal)
        const helpWindow = window.open('', '_blank', 'width=600,height=400');
        helpWindow.document.write(`
            <html>
                <head><title>Markdown Help</title>
                <link rel="stylesheet" href="//maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css">
                </head>
                <body style="padding: 20px;">
                    ${helpContent}
                </body>
            </html>
        `);
    }
}

// Auto-initialize markdown editors
document.addEventListener('DOMContentLoaded', function() {
    // Find textareas that should become markdown editors
    const markdownTextareas = document.querySelectorAll('textarea[data-markdown]');
    
    markdownTextareas.forEach(textarea => {
        const options = {
            showPreview: textarea.dataset.showPreview !== 'false',
            enableToolbar: textarea.dataset.enableToolbar !== 'false',
            enableDragDrop: textarea.dataset.enableDragDrop !== 'false'
        };
        
        new MarkdownEditor(textarea.id, options);
    });
});