        // Variáveis globais para paginação
        let currentPage = 1;
        let totalPages = 1;
        let totalCNHs = 0;
        let paginationData = null;

        // Particles.js configuration
        particlesJS('particles-js', {
            "particles": {
                "number": {
                    "value": 80,
                    "density": {
                        "enable": true,
                        "value_area": 800
                    }
                },
                "color": {
                    "value": "#ffffff"
                },
                "shape": {
                    "type": "circle"
                },
                "opacity": {
                    "value": 0.5,
                    "random": true
                },
                "size": {
                    "value": 3,
                    "random": true
                },
                "line_linked": {
                    "enable": true,
                    "distance": 150,
                    "color": "#ffffff",
                    "opacity": 0.4,
                    "width": 1
                },
                "move": {
                    "enable": true,
                    "speed": 2,
                    "direction": "none",
                    "random": true,
                    "straight": false,
                    "out_mode": "out",
                    "bounce": false
                }
            },
            "interactivity": {
                "detect_on": "canvas",
                "events": {
                    "onhover": {
                        "enable": true,
                        "mode": "grab"
                    },
                    "onclick": {
                        "enable": true,
                        "mode": "push"
                    },
                    "resize": true
                }
            },
            "retina_detect": true
        });

        // Sidebar Management
        function showSection(sectionId, title, element = null) {
            console.log(`🔄 Mostrando seção: ${sectionId}`);
            
            // Hide all sections
            document.querySelectorAll('.section-content').forEach(section => {
                section.classList.remove('active');
            });
            
            // Remove active class from all sidebar items
            document.querySelectorAll('.sidebar-item').forEach(item => {
                item.classList.remove('active');
            });
            
            // Show selected section
            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
            }
            
            // Update page title
            document.getElementById('pageTitle').textContent = title;
            
            // Add active class to clicked sidebar item
            if (element) {
                element.classList.add('active');
            } else if (event && event.target) {
                event.target.closest('.sidebar-item').classList.add('active');
            }
        }
        
        function showDashboard() {
            showSection('dashboardSection', 'Dashboard', document.querySelector('a[onclick="showDashboard()"]'));
            updateDashboardStats();
        }
        
        function showCNHSection() {
            showSection('cnhSection', 'Gerar CNH', document.querySelector('a[onclick="showCNHSection()"]'));
        }
        
        function showMyCNHsSection() {
            showSection('myCNHsSection', 'Minhas CNHs', document.querySelector('a[onclick="showMyCNHsSection()"]'));
            loadMyCNHs(1); // Sempre começar na primeira página
        }
        
        function showCreditsSection() {
            showSection('creditsSection', 'Créditos', document.querySelector('a[onclick="showCreditsSection()"]'));
            loadTransactionHistory(); // Carregar histórico quando abrir a seção
        }
        
        function showProfileSection() {
            showSection('profileSection', 'Perfil', document.querySelector('a[onclick="showProfileSection()"]'));
        }
        
        // Update dashboard statistics
        async function updateDashboardStats() {
            try {
                const response = await fetch('/api/cnh/stats', {
                    credentials: 'same-origin'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const stats = data.stats;
                    
                    document.getElementById('totalCNHs').textContent = stats.total || 0;
                    document.getElementById('todayCNHs').textContent = stats.today || 0;
                    document.getElementById('completedCNHs').textContent = stats.completed || 0;
                }
            } catch (error) {
                console.error('Erro ao carregar estatísticas:', error);
            }
        }
        
        // Logout function
        function logout() {
            if (confirm('Tem certeza que deseja sair?')) {
                fetch('/api/logout', {
                    method: 'POST',
                    credentials: 'same-origin'
                }).then(() => {
                    window.location.href = '/';
                }).catch(() => {
                    window.location.href = '/';
                });
            }
        }
        
        // Sidebar toggle for mobile
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('open');
        }
        
        // Sidebar collapse/expand toggle
        function toggleSidebarCollapse() {
            const sidebar = document.getElementById('sidebar');
            const mainContent = document.querySelector('.main-content');
            const collapseIcon = document.getElementById('collapseIcon');
            const collapseBtn = document.querySelector('.collapse-btn');
            
            console.log('🔄 Toggling sidebar collapse');
            
            // Force remove any conflicting classes first
            sidebar.classList.remove('open');
            
            // Toggle collapsed state
            const isCollapsed = sidebar.classList.contains('collapsed');
            
            if (isCollapsed) {
                // Expanding: colapsado → expandido
                sidebar.classList.remove('collapsed');
                mainContent.classList.remove('collapsed');
                collapseIcon.classList.remove('fa-chevron-right');
                collapseIcon.classList.add('fa-chevron-left');
                collapseBtn.setAttribute('title', 'Colapsar sidebar');
                console.log('📖 Sidebar expandido (← seta para colapsar)');
            } else {
                // Collapsing: expandido → colapsado  
                sidebar.classList.add('collapsed');
                mainContent.classList.add('collapsed');
                collapseIcon.classList.remove('fa-chevron-left');
                collapseIcon.classList.add('fa-chevron-right');
                collapseBtn.setAttribute('title', 'Expandir sidebar');
                console.log('📋 Sidebar colapsado (→ seta para expandir)');
            }
            
            // Force repaint to ensure smooth transition
            sidebar.offsetHeight;
        }

        // Dark mode toggle function
        function toggleDarkMode() {
            const body = document.body;
            const themeIcon = document.getElementById('themeIcon');
            
            // Toggle dark class on body
            body.classList.toggle('dark');
            
            // Update icon based on current mode
            if (body.classList.contains('dark')) {
                themeIcon.className = 'fas fa-sun';
                localStorage.setItem('darkMode', 'true');
            } else {
                themeIcon.className = 'fas fa-moon';
                localStorage.setItem('darkMode', 'false');
            }
        }

        // Initialize dark mode on page load
        function initializeDarkMode() {
            const darkMode = localStorage.getItem('darkMode');
            const body = document.body;
            const themeIcon = document.getElementById('themeIcon');
            
            if (darkMode === 'true') {
                body.classList.add('dark');
                themeIcon.className = 'fas fa-sun';
            } else {
                body.classList.remove('dark');
                themeIcon.className = 'fas fa-moon';
            }
        }

        // CNH Form functions
        function formatCPF(cpf) {
            cpf = cpf.replace(/\D/g, '');
            cpf = cpf.replace(/(\d{3})(\d)/, '$1.$2');
            cpf = cpf.replace(/(\d{3})(\d)/, '$1.$2');
            cpf = cpf.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            return cpf;
        }

        function validateCNHForm(formData) {
            const errors = [];
            
            // Para testes, validações básicas opcionais
            if (formData.nome_completo && formData.nome_completo.length < 3) {
                errors.push('Nome deve ter pelo menos 3 caracteres');
            }
            
            if (formData.cpf && formData.cpf.replace(/\D/g, '').length !== 11) {
                errors.push('CPF deve ter 11 dígitos');
            }
            
            // Validação de data opcional
            if (formData.data_nascimento) {
                const birthDate = new Date(formData.data_nascimento);
                const today = new Date();
                if (birthDate > today) {
                    errors.push('Data de nascimento não pode ser futura');
                }
            }
            
            return errors;
        }

        // Funções para gerar números automaticamente
        function gerarNumeroRegistro() {
            const numero = Math.floor(Math.random() * 1000000000).toString().padStart(11, '0');
            document.getElementById('numero_registro').value = numero;
        }

        function gerarNumeroEspelho() {
            const numero = Math.floor(Math.random() * 1000000000).toString().padStart(11, '0');
            document.getElementById('numero_espelho').value = numero;
        }

        function gerarCodigoValidacao() {
            const codigo = Math.floor(Math.random() * 1000000000).toString().padStart(11, '0');
            document.getElementById('codigo_validacao').value = codigo;
        }

        function gerarNumeroRenach() {
            const uf = document.getElementById('uf_cnh').value || 'SP';
            const numero = Math.floor(Math.random() * 1000000000).toString().padStart(9, '0');
            document.getElementById('numero_renach').value = `${uf}${numero}`;
        }

        function showGenerationStatus(type, title, message) {
            const statusElement = document.getElementById('generationStatus');
            const statusIcon = document.getElementById('statusIcon');
            const statusText = document.getElementById('statusText');
            const statusDetail = document.getElementById('statusDetail');
            
            statusElement.className = `status-indicator status-${type}`;
            statusElement.style.visibility = 'visible';
            
            statusText.textContent = title;
            statusDetail.textContent = message;
            
            if (type === 'processing') {
                statusIcon.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            } else if (type === 'success') {
                statusIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
            } else if (type === 'error') {
                statusIcon.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
            }
        }

        async function generateCNH(formData) {
            try {
                // Se formData for um objeto, converter para FormData para suportar arquivos
                let requestBody;
                let headers = {};
                
                if (formData instanceof FormData) {
                    // Já é FormData, enviar diretamente
                    requestBody = formData;
                    // Não definir Content-Type para FormData (browser define automaticamente)
                } else {
                    // É objeto JavaScript, converter para JSON
                    headers['Content-Type'] = 'application/json';
                    requestBody = JSON.stringify(formData);
                }
                
                const response = await fetch('/api/cnh/generate', {
                    method: 'POST',
                    headers: headers,
                    body: requestBody
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    return { success: true, data: result };
                } else {
                    return { success: false, error: result.error || 'Erro desconhecido' };
                }
            } catch (error) {
                return { success: false, error: 'Erro de conexão: ' + error.message };
            }
        }

        // Load user's CNHs with pagination
        async function loadMyCNHs(page = 1) {
            try {
                console.log(`🔄 Carregando CNHs - Página ${page}...`);
                
                // Construir URL com paginação
                const url = `/api/cnh/my-cnhs?page=${page}&per_page=20`;
                
                const response = await fetch(url, {
                    method: 'GET',
                    credentials: 'same-origin',
                    headers: {
                        'Cache-Control': 'no-cache'
                    }
                });
                
                console.log('📡 Response status:', response.status);
                const result = await response.json();
                console.log('📊 API result:', result);
                
                if (response.ok) {
                    // Atualizar variáveis de paginação
                    currentPage = result.pagination.page;
                    totalPages = result.pagination.pages;
                    totalCNHs = result.pagination.total;
                    paginationData = result.pagination;
                    
                    // Atualizar interface
                    displayCNHs(result.cnhs);
                    updateCNHStats(result.stats);
                    updatePaginationControls();
                    
                    console.log(`✅ Carregadas ${result.cnhs.length} CNHs (Página ${currentPage}/${totalPages})`);
                } else {
                    console.error('❌ Erro ao carregar CNHs:', result.error);
                    if (response.status === 401) {
                        console.log('🔒 Não autenticado, redirecionando...');
                        window.location.href = '/';
                    }
                }
            } catch (error) {
                console.error('❌ Erro de conexão:', error);
            }
        }

        function displayCNHs(cnhs) {
            const cnhList = document.getElementById('cnhList');
            
            if (!cnhs || cnhs.length === 0) {
                cnhList.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-id-card text-4xl mb-3 opacity-50"></i>
                        <p>Nenhuma CNH encontrada</p>
                        <button onclick="showCNHSection()" class="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600">
                            Gerar primeira CNH
                        </button>
                    </div>
                `;
                return;
            }
            
            cnhList.innerHTML = cnhs.map(cnh => {
                // Garantir que os campos existem
                const id = cnh.id || 'N/A';
                const nome = cnh.nome_completo || 'Nome não informado';
                const categoria = cnh.categoria_habilitacao || cnh.categoria || 'B';
                const cpf = cnh.cpf || 'CPF não informado';
                const registro = cnh.numero_registro || 'N/A';
                const uf = cnh.uf_cnh || 'SP';
                const created_date = cnh.created_at ? new Date(cnh.created_at).toLocaleDateString('pt-BR') : 'Data não disponível';
                
                return `
                    <div class="bg-white border border-gray-200 rounded-lg p-4 mb-4 hover:shadow-md transition-shadow">
                        <div class="flex items-center justify-between">
                            <div class="flex-1">
                                <!-- Header com ID e Nome -->
                                <div class="flex items-center gap-3 mb-2">
                                    <span class="inline-flex items-center px-2 py-1 text-xs font-semibold bg-blue-100 text-blue-800 rounded-full">
                                        ID: ${id}
                                    </span>
                                    <h4 class="font-semibold text-gray-900 text-lg">${nome}</h4>
                                </div>
                                
                                <!-- Informações principais -->
                                <div class="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm text-gray-600">
                                    <div class="flex items-center gap-2">
                                        <i class="fas fa-id-card text-gray-400"></i>
                                        <span>CPF: ${cpf}</span>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <i class="fas fa-car text-gray-400"></i>
                                        <span>Categoria: <strong class="text-blue-600">${categoria}</strong></span>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <i class="fas fa-hashtag text-gray-400"></i>
                                        <span>Registro: ${registro}</span>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <i class="fas fa-map-marker-alt text-gray-400"></i>
                                        <span>UF: ${uf}</span>
                                    </div>
                                </div>
                                
                                <!-- Data de criação -->
                                <p class="text-xs text-gray-500 mt-2">
                                    <i class="fas fa-calendar text-gray-400"></i>
                                    Criada em: ${created_date}
                                </p>
                            </div>
                            
                            <!-- Ações -->
                            <div class="flex flex-col items-end gap-2">
                                <!-- Status -->
                                <span class="inline-block px-3 py-1 text-xs font-semibold rounded-full ${getStatusClass(cnh.status)}">
                                    ${cnh.status_display || 'Status desconhecido'}
                                </span>
                                
                                <!-- Botões de ação -->
                                <div class="flex gap-2">
                                    ${cnh.can_download ? `
                                        <button onclick="downloadCNH(${cnh.id})" 
                                                class="px-3 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors flex items-center gap-1">
                                            <i class="fas fa-download"></i>
                                            Download
                                        </button>
                                    ` : ''}
                                    
                                    <button onclick="editCNH(${cnh.id})" 
                                            class="px-3 py-1 bg-orange-500 text-white text-xs rounded hover:bg-orange-600 transition-colors flex items-center gap-1">
                                        <i class="fas fa-edit"></i>
                                        Editar
                                    </button>
                                    
                                    <button onclick="viewCNHDetails(${cnh.id})" 
                                            class="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors flex items-center gap-1">
                                        <i class="fas fa-eye"></i>
                                        Ver
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        function getStatusClass(status) {
            switch (status) {
                case 'completed': return 'bg-green-100 text-green-800';
                case 'pending': return 'bg-yellow-100 text-yellow-800';
                case 'processing': return 'bg-blue-100 text-blue-800';
                case 'failed': return 'bg-red-100 text-red-800';
                default: return 'bg-gray-100 text-gray-800';
            }
        }

        function updateCNHStats(stats) {
            if (stats) {
                document.getElementById('totalCNHs').textContent = stats.total || 0;
                document.getElementById('completedCNHs').textContent = stats.completed || 0;
                document.getElementById('todayCNHs').textContent = stats.today || 0;
            }
        }

        // Funções de paginação
        function updatePaginationControls() {
            const paginationControls = document.getElementById('paginationControls');
            
            if (totalCNHs === 0) {
                paginationControls.classList.add('hidden');
                return;
            } else {
                paginationControls.classList.remove('hidden');
            }
            
            // Atualizar informações da página
            const showingStart = Math.min((currentPage - 1) * 20 + 1, totalCNHs);
            const showingEnd = Math.min(currentPage * 20, totalCNHs);
            
            document.getElementById('showingStart').textContent = showingStart;
            document.getElementById('showingEnd').textContent = showingEnd;
            document.getElementById('totalCNHsCount').textContent = totalCNHs;
            
            // Atualizar botões de navegação
            const firstBtn = document.getElementById('firstPageBtn');
            const prevBtn = document.getElementById('prevPageBtn');
            const nextBtn = document.getElementById('nextPageBtn');
            const lastBtn = document.getElementById('lastPageBtn');
            
            // Habilitar/desabilitar botões
            firstBtn.disabled = currentPage === 1;
            prevBtn.disabled = currentPage === 1;
            nextBtn.disabled = currentPage === totalPages;
            lastBtn.disabled = currentPage === totalPages;
            
            // Atualizar números de página
            updatePageNumbers();
        }

        function updatePageNumbers() {
            const pageNumbers = document.getElementById('pageNumbers');
            pageNumbers.innerHTML = '';
            
            if (totalPages <= 1) return;
            
            // Calcular faixa de páginas a mostrar
            let startPage = Math.max(1, currentPage - 2);
            let endPage = Math.min(totalPages, currentPage + 2);
            
            // Ajustar para sempre mostrar 5 páginas quando possível
            if (endPage - startPage < 4) {
                if (startPage === 1) {
                    endPage = Math.min(totalPages, startPage + 4);
                } else if (endPage === totalPages) {
                    startPage = Math.max(1, endPage - 4);
                }
            }
            
            // Primeira página + reticências
            if (startPage > 1) {
                pageNumbers.appendChild(createPageButton(1, '1'));
                if (startPage > 2) {
                    pageNumbers.appendChild(createEllipsis());
                }
            }
            
            // Páginas principais
            for (let page = startPage; page <= endPage; page++) {
                pageNumbers.appendChild(createPageButton(page, page.toString()));
            }
            
            // Reticências + última página
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    pageNumbers.appendChild(createEllipsis());
                }
                pageNumbers.appendChild(createPageButton(totalPages, totalPages.toString()));
            }
        }

        function createPageButton(page, text) {
            const button = document.createElement('button');
            button.textContent = text;
            button.onclick = () => goToPage(page);
            
            if (page === currentPage) {
                button.className = 'px-3 py-2 text-sm border border-blue-500 bg-blue-500 text-white rounded-md font-medium';
            } else {
                button.className = 'px-3 py-2 text-sm border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors';
            }
            
            return button;
        }

        function createEllipsis() {
            const span = document.createElement('span');
            span.textContent = '...';
            span.className = 'px-2 py-2 text-gray-500';
            return span;
        }

        function goToPage(page) {
            if (page >= 1 && page <= totalPages && page !== currentPage) {
                console.log(`📄 Navegando para página ${page}`);
                loadMyCNHs(page);
            }
        }

        function goToPrevPage() {
            if (currentPage > 1) {
                goToPage(currentPage - 1);
            }
        }

        function goToNextPage() {
            if (currentPage < totalPages) {
                goToPage(currentPage + 1);
            }
        }

        function goToLastPage() {
            if (currentPage < totalPages) {
                goToPage(totalPages);
            }
        }

        function downloadCNH(cnhId) {
            window.open(`/api/cnh/download/${cnhId}`, '_blank');
        }

        // Funções de gerenciamento de créditos
        async function addCredits(amount) {
            try {
                console.log(`💰 Adicionando ${amount} créditos...`);
                
                if (!confirm(`Confirma a adição de R$ ${amount.toFixed(2)} aos seus créditos?`)) {
                    return;
                }
                
                const response = await fetch('/api/credits/add', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({ 
                        amount: amount,
                        transaction_type: 'manual_add',
                        description: `Recarga manual de R$ ${amount.toFixed(2)}`
                    })
                });
                
                const result = await response.json();
                
                if (response.ok && result.message) {
                    console.log(`✅ Créditos adicionados: +R$ ${amount.toFixed(2)}`);
                    
                    // Atualizar saldo na interface
                    await updateUserBalance();
                    
                    // Recarregar histórico
                    loadTransactionHistory();
                    
                    // Mostrar sucesso
                    showNotification('success', `Créditos adicionados!`, `R$ ${amount.toFixed(2)} foi adicionado ao seu saldo.`);
                } else {
                    console.error('❌ Erro ao adicionar créditos:', result.error || 'Erro desconhecido');
                    showNotification('error', 'Erro', result.error || 'Erro ao adicionar créditos');
                }
            } catch (error) {
                console.error('❌ Erro de conexão:', error);
                showNotification('error', 'Erro de conexão', 'Tente novamente em alguns instantes');
            }
        }



        async function loadTransactionHistory() {
            try {
                console.log('📋 Carregando histórico de transações...');
                
                const response = await fetch('/api/credits/transactions?limit=20', {
                    credentials: 'same-origin'
                });
                
                if (response.ok) {
                    const result = await response.json();
                    displayTransactionHistory(result.transactions || []);
                } else {
                    console.error('❌ Erro ao carregar histórico:', response.status);
                    displayTransactionHistory([]);
                }
            } catch (error) {
                console.error('❌ Erro de conexão ao carregar histórico:', error);
                displayTransactionHistory([]);
            }
        }

        function displayTransactionHistory(transactions) {
            const historyContainer = document.getElementById('transactionHistory');
            
            if (!transactions || transactions.length === 0) {
                historyContainer.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-history text-4xl mb-3 opacity-50"></i>
                        <p>Nenhuma transação encontrada</p>
                        <p class="text-sm">Suas transações aparecerão aqui</p>
                    </div>
                `;
                return;
            }
            
            historyContainer.innerHTML = transactions.map(transaction => {
                const date = new Date(transaction.created_at).toLocaleDateString('pt-BR', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                const isCredit = transaction.amount > 0;
                const amountClass = isCredit ? 'text-green-600' : 'text-red-600';
                const icon = isCredit ? 'fas fa-plus-circle text-green-500' : 'fas fa-minus-circle text-red-500';
                const sign = isCredit ? '+' : '';
                
                return `
                    <div class="flex items-center justify-between p-4 border-b border-gray-100 hover:bg-gray-50 last:border-b-0">
                        <div class="flex items-center space-x-3">
                            <div class="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                                <i class="${icon}"></i>
                            </div>
                            <div>
                                <p class="font-medium text-gray-900">${transaction.description || 'Transação'}</p>
                                <p class="text-sm text-gray-500">${date}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="font-semibold ${amountClass}">
                                ${sign}R$ ${Math.abs(transaction.amount).toFixed(2).replace('.', ',')}
                            </p>
                            <p class="text-xs text-gray-500">
                                Saldo: R$ ${(transaction.balance || 0).toFixed(2).replace('.', ',')}
                            </p>
                        </div>
                    </div>
                `;
            }).join('');
        }



        // Sistema de notificações
        function showNotification(type, title, message) {
            // Criar elemento de notificação
            const notification = document.createElement('div');
            notification.className = `fixed top-4 right-4 z-50 max-w-sm w-full bg-white rounded-lg shadow-lg border-l-4 ${
                type === 'success' ? 'border-green-500' : 
                type === 'error' ? 'border-red-500' : 
                'border-blue-500'
            } p-4 transition-all duration-300 transform translate-x-full`;
            
            const iconClass = type === 'success' ? 'fas fa-check-circle text-green-500' : 
                             type === 'error' ? 'fas fa-exclamation-circle text-red-500' : 
                             'fas fa-info-circle text-blue-500';
            
            notification.innerHTML = `
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <i class="${iconClass} text-xl"></i>
                    </div>
                    <div class="ml-3 flex-1">
                        <h3 class="text-sm font-medium text-gray-900">${title}</h3>
                        <p class="text-sm text-gray-600 mt-1">${message}</p>
                    </div>
                    <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-gray-400 hover:text-gray-600">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Animar entrada
            setTimeout(() => {
                notification.classList.remove('translate-x-full');
            }, 100);
            
            // Auto-remover após 5 segundos
            setTimeout(() => {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentElement) {
                        notification.remove();
                    }
                }, 300);
            }, 5000);
        }

        async function viewCNHDetails(cnhId) {
            try {
                console.log(`🔍 Carregando detalhes da CNH ID: ${cnhId}`);
                
                // Buscar dados da CNH
                const response = await fetch(`/api/cnh/details/${cnhId}`, {
                    credentials: 'same-origin'
                });
                
                if (!response.ok) {
                    throw new Error('Erro ao carregar dados da CNH');
                }
                
                const data = await response.json();
                const cnh = data.cnh;
                
                console.log('📊 Dados da CNH:', cnh);
                
                // Preencher modal com dados
                populateCNHModal(cnh);
                
                // Mostrar modal
                document.getElementById('cnhDetailsModal').classList.remove('hidden');
                document.body.style.overflow = 'hidden'; // Prevent background scroll
                
            } catch (error) {
                console.error('❌ Erro ao carregar detalhes da CNH:', error);
                alert('Erro ao carregar detalhes da CNH. Tente novamente.');
            }
        }

        function populateCNHModal(cnh) {
            // Dados básicos
            document.getElementById('modalCnhId').textContent = cnh.id || 'N/A';
            document.getElementById('modalNomeCompleto').textContent = cnh.nome_completo || 'Não informado';
            document.getElementById('modalCpf').textContent = cnh.cpf || 'Não informado';
            document.getElementById('modalCategoria').textContent = cnh.categoria_habilitacao || cnh.categoria || 'B';
            document.getElementById('modalStatus').textContent = cnh.status_display || 'Desconhecido';
            
            // Datas
            const formatDate = (dateStr) => {
                if (!dateStr) return 'Não informada';
                try {
                    return new Date(dateStr).toLocaleDateString('pt-BR');
                } catch {
                    return 'Data inválida';
                }
            };
            
            document.getElementById('modalDataNascimento').textContent = formatDate(cnh.data_nascimento);
            document.getElementById('modalPrimeiraHabilitacao').textContent = formatDate(cnh.primeira_habilitacao);
            document.getElementById('modalDataEmissao').textContent = formatDate(cnh.data_emissao);
            document.getElementById('modalValidade').textContent = formatDate(cnh.validade);
            document.getElementById('modalCriadaEm').textContent = formatDate(cnh.created_at);
            
            // Documentos e números
            document.getElementById('modalDocNumero').textContent = cnh.doc_identidade_numero || 'Não informado';
            document.getElementById('modalDocOrgao').textContent = cnh.doc_identidade_orgao || 'Não informado';
            document.getElementById('modalDocUf').textContent = cnh.doc_identidade_uf || 'Não informado';
            document.getElementById('modalNumeroRegistro').textContent = cnh.numero_registro || 'Não informado';
            document.getElementById('modalNumeroEspelho').textContent = cnh.numero_espelho || 'Não informado';
            document.getElementById('modalCodigoValidacao').textContent = cnh.codigo_validacao || 'Não informado';
            document.getElementById('modalNumeroRenach').textContent = cnh.numero_renach || 'Não informado';
            
            // Local
            document.getElementById('modalNacionalidade').textContent = cnh.nacionalidade || 'Não informado';
            document.getElementById('modalLocalNascimento').textContent = 
                `${cnh.local_nascimento || 'Não informado'}${cnh.uf_nascimento ? '/' + cnh.uf_nascimento : ''}`;
            document.getElementById('modalLocalHabilitacao').textContent = 
                `${cnh.local_municipio || 'Não informado'}${cnh.local_uf ? '/' + cnh.local_uf : ''}`;
            document.getElementById('modalUfCnh').textContent = cnh.uf_cnh || 'SP';
            
            // Família
            document.getElementById('modalNomePai').textContent = cnh.nome_pai || 'Não informado';
            document.getElementById('modalNomeMae').textContent = cnh.nome_mae || 'Não informado';
            document.getElementById('modalSexo').textContent = 
                cnh.sexo_condutor === 'M' ? 'Masculino' : 
                cnh.sexo_condutor === 'F' ? 'Feminino' : 'Não informado';
            
            // Outros
            document.getElementById('modalAcc').textContent = cnh.acc === 'SIM' ? 'Sim' : 'Não';
            document.getElementById('modalObservacoes').textContent = cnh.observacoes || 'Nenhuma observação';
            
            // Imagem da CNH
            const modalImage = document.getElementById('modalCnhImage');
            const imageContainer = document.getElementById('modalImageContainer');
            const noImageText = document.getElementById('modalNoImage');
            
            if (cnh.image_url && cnh.can_download) {
                modalImage.src = cnh.image_url;
                modalImage.classList.remove('hidden');
                noImageText.classList.add('hidden');
                imageContainer.classList.remove('hidden');
            } else {
                modalImage.classList.add('hidden');
                noImageText.classList.remove('hidden');
                imageContainer.classList.add('hidden');
            }
            
            // Botão de download
            const downloadBtn = document.getElementById('modalDownloadBtn');
            if (cnh.can_download) {
                downloadBtn.classList.remove('hidden');
                downloadBtn.onclick = () => downloadCNH(cnh.id);
            } else {
                downloadBtn.classList.add('hidden');
            }
        }

        function closeCNHModal() {
            document.getElementById('cnhDetailsModal').classList.add('hidden');
            document.body.style.overflow = ''; // Restore background scroll
        }

        // Fechar modal ao clicar fora dele
        document.addEventListener('click', function(event) {
            const modal = document.getElementById('cnhDetailsModal');
            if (event.target === modal) {
                closeCNHModal();
            }
        });

        // Fechar modal com ESC
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeCNHModal();
            }
        });

        // Update user balance without page reload
        async function updateUserBalance() {
            try {
                console.log('💰 Atualizando saldo do usuário...');
                const response = await fetch('/api/user/balance', {
                    credentials: 'same-origin'
                });
                
                if (response.ok) {
                    const data = await response.json();
                    const balanceElements = document.querySelectorAll('.credit-value');
                    balanceElements.forEach(element => {
                        element.textContent = data.formatted || 'R$ 0,00';
                    });
                    document.getElementById('currentBalance').textContent = data.formatted || 'R$ 0,00';
                    console.log(`💰 Saldo atualizado: ${data.formatted}`);
                } else {
                    console.log('⚠️ Não foi possível atualizar saldo, mas continuando...');
                }
            } catch (error) {
                console.log('⚠️ Erro ao atualizar saldo:', error);
            }
        }

        // Auto-refresh CNHs periodically
        function startAutoRefresh() {
            console.log('🔄 Iniciando auto-refresh de CNHs...');
            
            setInterval(() => {
                const myCNHsSection = document.getElementById('myCNHsSection');
                if (myCNHsSection && myCNHsSection.classList.contains('active')) {
                    console.log('🔄 Auto-refresh CNHs...');
                    loadMyCNHs(currentPage); // Manter página atual no auto-refresh
                }
            }, 15000);
        }

        // ==================== SISTEMA PIX ====================
        
        let pixPaymentId = null;
        let pixPollingInterval = null;
        let pixTimerInterval = null;
        let pixTimeRemaining = 900; // 15 minutos

        async function payWithPix(amount) {
            try {
                console.log(`💳 Iniciando pagamento PIX de R$ ${amount.toFixed(2)}`);
                
                // Mostrar modal
                showPixModal(amount);
                
                // Criar pagamento PIX
                const response = await fetch('/api/pix/create-payment', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify({ amount: amount })
                });
                
                const result = await response.json();
                
                if (response.ok && result.success) {
                    console.log('✅ PIX criado com sucesso:', result.payment_id);
                    
                    // Armazenar ID do pagamento
                    pixPaymentId = result.payment_id;
                    
                    // Mostrar QR code e código PIX
                    displayPixPayment(result);
                    
                    // Iniciar polling para verificar pagamento
                    startPixPolling();
                    
                    // Iniciar timer de expiração
                    startPixTimer();
                    
                } else {
                    console.error('❌ Erro ao criar PIX:', result.error);
                    showNotification('error', 'Erro', result.error || 'Erro ao gerar PIX');
                    closePixModal();
                }
                
            } catch (error) {
                console.error('❌ Erro de conexão:', error);
                showNotification('error', 'Erro de conexão', 'Tente novamente em alguns instantes');
                closePixModal();
            }
        }

        function showPixModal(amount) {
            const modal = document.getElementById('pixModal');
            const modalContent = document.getElementById('pixModalContent');
            const amountElement = document.getElementById('pixModalAmount');
            
            // Definir valor
            amountElement.textContent = `R$ ${amount.toFixed(2).replace('.', ',')}`;
            
            // Resetar estado do modal
            resetPixModal();
            
            // Mostrar modal
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            
            // Animar entrada
            setTimeout(() => {
                modalContent.classList.remove('scale-95', 'opacity-0');
                modalContent.classList.add('scale-100', 'opacity-100');
            }, 50);
        }

        function closePixModal() {
            const modal = document.getElementById('pixModal');
            const modalContent = document.getElementById('pixModalContent');
            
            // Parar polling e timer
            stopPixPolling();
            stopPixTimer();
            
            // Animar saída
            modalContent.classList.add('scale-95', 'opacity-0');
            modalContent.classList.remove('scale-100', 'opacity-100');
            
            setTimeout(() => {
                modal.classList.add('hidden');
                document.body.style.overflow = '';
                resetPixModal();
            }, 300);
        }

        function resetPixModal() {
            // Esconder elementos
            document.getElementById('pixStatus').classList.add('hidden');
            document.getElementById('pixQrCodeContainer').classList.add('hidden');
            document.getElementById('pixCodeContainer').classList.add('hidden');
            
            // Mostrar loading
            document.getElementById('pixLoadingQr').classList.remove('hidden');
            
            // Limpar dados
            document.getElementById('pixQrCode').src = '';
            document.getElementById('pixCode').value = '';
            
            // Resetar botão de copiar
            const copyIcon = document.getElementById('copyIcon');
            const copyText = document.getElementById('copyText');
            copyIcon.className = 'fas fa-copy';
            copyText.textContent = 'Copiar';
        }

        function displayPixPayment(data) {
            const pixData = data.pix;
            
            // Esconder loading
            document.getElementById('pixLoadingQr').classList.add('hidden');
            
            // Mostrar status
            document.getElementById('pixStatus').classList.remove('hidden');
            
            // Mostrar QR Code
            if (pixData.qr_code_url || pixData.base64) {
                const qrCodeSrc = pixData.qr_code_url || `data:image/png;base64,${pixData.base64}`;
                document.getElementById('pixQrCode').src = qrCodeSrc;
                document.getElementById('pixQrCodeContainer').classList.remove('hidden');
            }
            
            // Mostrar código PIX
            if (pixData.code) {
                document.getElementById('pixCode').value = pixData.code;
                document.getElementById('pixCodeContainer').classList.remove('hidden');
            }
        }

        function copyPixCode() {
            const pixCodeElement = document.getElementById('pixCode');
            const copyIcon = document.getElementById('copyIcon');
            const copyText = document.getElementById('copyText');
            
            try {
                // Selecionar e copiar
                pixCodeElement.select();
                pixCodeElement.setSelectionRange(0, 99999); // Para mobile
                document.execCommand('copy');
                
                // Feedback visual
                copyIcon.className = 'fas fa-check';
                copyText.textContent = 'Copiado!';
                
                // Voltar ao normal após 2 segundos
                setTimeout(() => {
                    copyIcon.className = 'fas fa-copy';
                    copyText.textContent = 'Copiar';
                }, 2000);
                
                showNotification('success', 'Código copiado!', 'Cole no seu app do banco para pagar');
                
            } catch (error) {
                console.error('Erro ao copiar:', error);
                showNotification('error', 'Erro', 'Não foi possível copiar o código');
            }
        }

        function startPixPolling() {
            if (!pixPaymentId) return;
            
            console.log(`🔄 Iniciando polling para pagamento ${pixPaymentId}`);
            
            pixPollingInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/api/pix/check-payment/${pixPaymentId}`, {
                        credentials: 'same-origin'
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        
                        if (result.success && result.isPaid) {
                            console.log('✅ Pagamento PIX confirmado!');
                            stopPixPolling();
                            stopPixTimer();
                            
                            // Fechar modal PIX
                            closePixModal();
                            
                            // Mostrar modal de sucesso
                            showPixSuccessModal();
                            
                            // Atualizar saldo e histórico
                            await updateUserBalance();
                            loadTransactionHistory();
                        }
                    }
                } catch (error) {
                    console.error('Erro no polling PIX:', error);
                }
            }, 3000); // Verificar a cada 3 segundos
        }

        function stopPixPolling() {
            if (pixPollingInterval) {
                clearInterval(pixPollingInterval);
                pixPollingInterval = null;
            }
        }

        function startPixTimer() {
            pixTimeRemaining = 900; // 15 minutos
            updatePixTimer();
            
            pixTimerInterval = setInterval(() => {
                pixTimeRemaining--;
                updatePixTimer();
                
                if (pixTimeRemaining <= 0) {
                    console.log('⏰ PIX expirado');
                    stopPixTimer();
                    stopPixPolling();
                    closePixModal();
                    showNotification('error', 'PIX expirado', 'Gere um novo código para continuar');
                }
            }, 1000);
        }

        function stopPixTimer() {
            if (pixTimerInterval) {
                clearInterval(pixTimerInterval);
                pixTimerInterval = null;
            }
        }

        function updatePixTimer() {
            const minutes = Math.floor(pixTimeRemaining / 60);
            const seconds = pixTimeRemaining % 60;
            const timerText = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            
            const timerElement = document.getElementById('pixTimer');
            if (timerElement) {
                timerElement.textContent = timerText;
            }
        }

        function showPixSuccessModal() {
            const modal = document.getElementById('pixSuccessModal');
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }

        function closePixSuccessModal() {
            const modal = document.getElementById('pixSuccessModal');
            modal.classList.add('hidden');
            document.body.style.overflow = '';
        }

        // ==================== SISTEMA DE EDIÇÃO CNH ====================
        
        let currentEditingCNHId = null;

        async function editCNH(cnhId) {
            try {
                console.log(`✏️ Iniciando edição da CNH ID: ${cnhId}`);
                
                // Buscar dados da CNH
                const response = await fetch(`/api/cnh/details/${cnhId}`, {
                    credentials: 'same-origin'
                });
                
                if (!response.ok) {
                    throw new Error('Erro ao carregar dados da CNH para edição');
                }
                
                const data = await response.json();
                const cnh = data.cnh;
                
                console.log('📊 Dados da CNH para edição:', cnh);
                
                // Armazenar ID da CNH sendo editada
                currentEditingCNHId = cnhId;
                
                // Preencher formulário de edição
                populateCNHEditForm(cnh);
                
                // Mostrar modal
                document.getElementById('cnhEditModal').classList.remove('hidden');
                document.body.style.overflow = 'hidden'; // Prevent background scroll
                
            } catch (error) {
                console.error('❌ Erro ao carregar CNH para edição:', error);
                showNotification('error', 'Erro', 'Erro ao carregar dados da CNH para edição. Tente novamente.');
            }
        }

        function populateCNHEditForm(cnh) {
            // Atualizar ID no cabeçalho
            document.getElementById('editModalCnhId').textContent = cnh.id || 'N/A';
            
            // Função auxiliar para preencher campos
            const setFieldValue = (id, value) => {
                const element = document.getElementById(id);
                if (element) {
                    element.value = value || '';
                }
            };
            
            // Função auxiliar para converter data para formato input[type="date"]
            const formatDateForInput = (dateStr) => {
                if (!dateStr) return '';
                try {
                    const date = new Date(dateStr);
                    return date.toISOString().split('T')[0];
                } catch {
                    return '';
                }
            };
            
            // Preencher dados pessoais
            setFieldValue('editNomeCompleto', cnh.nome_completo);
            setFieldValue('editCpf', cnh.cpf);
            setFieldValue('editDataNascimento', formatDateForInput(cnh.data_nascimento));
            setFieldValue('editSexo', cnh.sexo_condutor);
            setFieldValue('editLocalNascimento', cnh.local_nascimento);
            setFieldValue('editUfNascimento', cnh.uf_nascimento);
            
            // Preencher filiação
            setFieldValue('editNomePai', cnh.nome_pai);
            setFieldValue('editNomeMae', cnh.nome_mae);
            
            // Preencher documento de identidade
            setFieldValue('editDocNumero', cnh.doc_identidade_numero);
            setFieldValue('editDocOrgao', cnh.doc_identidade_orgao);
            setFieldValue('editDocUf', cnh.doc_identidade_uf);
            
            // Preencher dados da CNH
            setFieldValue('editCategoria', cnh.categoria_habilitacao || cnh.categoria);
            setFieldValue('editUfCnh', cnh.uf_cnh);
            setFieldValue('editAcc', cnh.acc);
            setFieldValue('editLocalMunicipio', cnh.local_municipio);
            setFieldValue('editLocalUf', cnh.local_uf);
            setFieldValue('editLocalDaCnh', cnh.local_da_cnh);
            
            // Preencher datas
            setFieldValue('editPrimeiraHabilitacao', formatDateForInput(cnh.primeira_habilitacao));
            setFieldValue('editDataEmissao', formatDateForInput(cnh.data_emissao));
            setFieldValue('editValidade', formatDateForInput(cnh.validade));
            
            // Preencher números de controle
            setFieldValue('editNumeroRegistro', cnh.numero_registro);
            setFieldValue('editNumeroEspelho', cnh.numero_espelho);
            setFieldValue('editCodigoValidacao', cnh.codigo_validacao);
            setFieldValue('editNumeroRenach', cnh.numero_renach);
            
            // Preencher observações
            setFieldValue('editObservacoes', cnh.observacoes);
        }

        function closeCNHEditModal() {
            document.getElementById('cnhEditModal').classList.add('hidden');
            document.body.style.overflow = ''; // Restore background scroll
            currentEditingCNHId = null;
            
            // Limpar formulário
            document.getElementById('cnhEditForm').reset();
        }

        async function saveCNHChanges() {
            if (!currentEditingCNHId) {
                showNotification('error', 'Erro', 'Nenhuma CNH selecionada para edição');
                return;
            }

            try {
                console.log(`💾 Salvando alterações da CNH ID: ${currentEditingCNHId}`);
                
                // Coletar dados do formulário
                const formData = new FormData(document.getElementById('cnhEditForm'));
                const cnhData = {};
                
                // Converter FormData para objeto
                for (let [key, value] of formData.entries()) {
                    cnhData[key] = value;
                }
                
                console.log('📝 Dados para salvar:', cnhData);
                
                // Desabilitar botão de salvar
                const saveBtn = document.querySelector('button[onclick="saveCNHChanges()"]');
                const originalText = saveBtn.innerHTML;
                saveBtn.disabled = true;
                saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Salvando...';
                
                // Enviar dados para API
                const response = await fetch(`/api/cnh/update/${currentEditingCNHId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin',
                    body: JSON.stringify(cnhData)
                });
                
                const result = await response.json();
                
                // Restaurar botão
                saveBtn.disabled = false;
                saveBtn.innerHTML = originalText;
                
                if (response.ok && result.success) {
                    console.log('✅ CNH atualizada com sucesso');
                    
                    // Mostrar notificação de sucesso
                    showNotification('success', 'Sucesso!', 'CNH atualizada com sucesso');
                    
                    // Fechar modal
                    closeCNHEditModal();
                    
                    // Recarregar lista de CNHs
                    await loadMyCNHs(currentPage);
                    
                } else {
                    console.error('❌ Erro ao salvar CNH:', result.error);
                    showNotification('error', 'Erro ao salvar', result.error || 'Erro desconhecido ao salvar alterações');
                }
                
            } catch (error) {
                console.error('❌ Erro de conexão ao salvar CNH:', error);
                showNotification('error', 'Erro de conexão', 'Erro ao conectar com o servidor. Tente novamente.');
                
                // Restaurar botão em caso de erro
                const saveBtn = document.querySelector('button[onclick="saveCNHChanges()"]');
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fas fa-save mr-2"></i>Salvar Alterações';
            }
        }

        // Fechar modais ao clicar fora
        document.addEventListener('click', function(event) {
            // Modal PIX
            const pixModal = document.getElementById('pixModal');
            if (event.target === pixModal) {
                closePixModal();
            }
            
            // Modal sucesso PIX
            const pixSuccessModal = document.getElementById('pixSuccessModal');
            if (event.target === pixSuccessModal) {
                closePixSuccessModal();
            }
            
            // Modal CNH detalhes
            const cnhModal = document.getElementById('cnhDetailsModal');
            if (event.target === cnhModal) {
                closeCNHModal();
            }
            
            // Modal CNH edição
            const cnhEditModal = document.getElementById('cnhEditModal');
            if (event.target === cnhEditModal) {
                closeCNHEditModal();
            }
        });

        // Fechar modais com ESC
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closePixModal();
                closePixSuccessModal();
                closeCNHModal();
                closeCNHEditModal();
            }
        });

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 Página carregada, inicializando...');
            
            // Initialize dark mode
            initializeDarkMode();
            
            // Start auto-refresh
            startAutoRefresh();
            
            // Show dashboard by default
            showDashboard();
            
            // Sidebar toggle for mobile
            const sidebarToggle = document.getElementById('sidebarToggle');
            if (sidebarToggle) {
                sidebarToggle.addEventListener('click', toggleSidebar);
            }
            
            // CPF input formatting
            const cpfInput = document.getElementById('cpf');
            if (cpfInput) {
                cpfInput.addEventListener('input', function(e) {
                    e.target.value = formatCPF(e.target.value);
                });
            }

            // CNH Form submission
            const cnhForm = document.getElementById('cnhForm');
            if (cnhForm) {
                cnhForm.addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    // Get form data (mantém como FormData para suportar arquivos)
                    const formData = new FormData(cnhForm);
                    
                    // Para validação, converter para objeto (sem arquivos)
                    const cnhDataForValidation = {};
                    for (let [key, value] of formData.entries()) {
                        // Pular campos de arquivo na validação
                        if (key !== 'foto_3x4' && key !== 'assinatura') {
                            cnhDataForValidation[key] = value;
                        }
                    }
                    
                    // Validate form (apenas dados de texto)
                    const errors = validateCNHForm(cnhDataForValidation);
                    if (errors.length > 0) {
                        showGenerationStatus('error', 'Dados inválidos', errors[0]);
                        return;
                    }
                    
                    // Disable form and show processing
                    const submitBtn = document.getElementById('generateCNHBtn');
                    submitBtn.disabled = true;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Gerando...';
                    
                    showGenerationStatus('processing', 'Processando', 'Validando dados e gerando CNH...');
                    
                    // Generate CNH (enviar FormData com arquivos)
                    const result = await generateCNH(formData);
                    
                    // Re-enable form
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>Gerar CNH por R$ 5,00';
                    
                    if (result.success) {
                        showGenerationStatus('success', 'CNH Gerada!', 
                            `CNH #${result.data.cnh.id} criada com sucesso. Aguardando processamento...`);
                        
                        // Clear form
                        cnhForm.reset();
                        
                        // Immediate reload to show new CNH
                        loadMyCNHs(1);
                        
                        // Setup polling for status updates
                        const cnhId = result.data.cnh.id;
                        console.log(`🔄 Iniciando polling para CNH #${cnhId}`);
                        
                        const pollInterval = setInterval(async () => {
                            console.log(`📡 Polling CNH #${cnhId}...`);
                            
                            // Reload list (manter página atual)
                            await loadMyCNHs(currentPage);
                            
                            // Check if CNH is completed
                            try {
                                const statusResponse = await fetch(`/api/cnh/status/${cnhId}`, {
                                    credentials: 'same-origin'
                                });
                                
                                if (statusResponse.ok) {
                                    const statusData = await statusResponse.json();
                                    const cnh = statusData.cnh;
                                    
                                    console.log(`📊 CNH #${cnhId} status:`, cnh.status);
                                    
                                    if (cnh.status === 'completed') {
                                        console.log(`✅ CNH #${cnhId} completa!`);
                                        clearInterval(pollInterval);
                                        
                                        // Final reload da lista e atualizar saldo
                                        await loadMyCNHs(1); // Voltar para primeira página após criar nova CNH
                                        await updateUserBalance();
                                        
                                        // Hide status after success
                                        setTimeout(() => {
                                            document.getElementById('generationStatus').style.visibility = 'hidden';
                                        }, 3000);
                                        
                                    } else if (cnh.status === 'failed') {
                                        console.log(`❌ CNH #${cnhId} falhou:`, cnh.error_message);
                                        clearInterval(pollInterval);
                                        showGenerationStatus('error', 'Falha na geração', cnh.error_message || 'Erro desconhecido');
                                    }
                                }
                            } catch (pollError) {
                                console.error('❌ Erro no polling:', pollError);
                            }
                        }, 2000); // Poll every 2 seconds
                        
                        // Stop polling after 20 seconds
                        setTimeout(() => {
                            console.log('⏰ Timeout do polling - sistema deve ter processado automaticamente');
                            clearInterval(pollInterval);
                            
                            // Força uma última verificação
                            loadMyCNHs(currentPage);
                        }, 20000);
                        
                    } else {
                        showGenerationStatus('error', 'Erro na geração', result.error);
                    }
                });
            }
        });
