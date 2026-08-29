// Organization Chart & Collapsible Tree View Controller (MS Teams / Workday Style)

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.teamManagerApp = function() {
    return {
        activeTab: 'org-chart', // 'org-chart' | 'tree' | 'directory'
        searchQuery: '',
        selectedDepartmentFilter: '',
        isLoading: true,
        
        // Data sources
        hierarchyData: { departments: [], standalone_teams: [] },
        orgChartNodes: [],
        orgTreeRoot: null,
        
        // Org Chart Canvas Controls
        zoomLevel: 1.0,
        collapsedNodes: {},
        selectedNode: null,
        
        // Modals
        showAddTeamModal: false,
        showAddDeptModal: false,
        showAssignMemberModal: false,
        showReportingModal: false,
        
        reportingForm: {
            user_id: null,
            user_name: '',
            current_manager_id: null,
            new_manager_id: null
        },
        
        toastMessage: '',
        toastType: 'info',
        showToastNotification: false,

        async init() {
            await this.loadAllData();
            if (window.lucide) lucide.createIcons();
            
            this.$watch('activeTab', () => {
                if (window.lucide) setTimeout(lucide.createIcons, 50);
            });
            this.$watch('searchQuery', () => {
                this.buildOrgTree();
            });
        },

        async loadAllData() {
            this.isLoading = true;
            try {
                const [hierRes, orgRes] = await Promise.all([
                    fetch('/teams/api/hierarchy/'),
                    fetch('/teams/api/org-chart/')
                ]);
                
                if (hierRes.ok) this.hierarchyData = await hierRes.json();
                if (orgRes.ok) {
                    const orgData = await orgRes.json();
                    this.orgChartNodes = orgData.nodes || [];
                    this.buildOrgTree();
                }
            } catch (err) {
                console.error("Failed to load organization data:", err);
                this.showToast("Failed to load organization data.", "error");
            } finally {
                this.isLoading = false;
                if (window.lucide) setTimeout(lucide.createIcons, 50);
            }
        },

        buildOrgTree() {
            if (!this.orgChartNodes || this.orgChartNodes.length === 0) {
                this.orgTreeRoot = null;
                return;
            }

            const nodeMap = {};
            this.orgChartNodes.forEach(node => {
                nodeMap[node.id] = {
                    ...node,
                    children: [],
                    _matchesSearch: this.isNodeMatchingSearch(node)
                };
            });

            let root = null;
            const roots = [];

            this.orgChartNodes.forEach(node => {
                const current = nodeMap[node.id];
                if (node.parent_id && nodeMap[node.parent_id]) {
                    nodeMap[node.parent_id].children.push(current);
                } else {
                    roots.push(current);
                }
            });

            // Find primary root (master admin 'aman' or first executive root)
            root = roots.find(r => r.is_master) || roots[0] || null;
            
            // If multiple disconnected roots exist, attach them under a virtual root or primary root
            if (roots.length > 1 && root) {
                roots.forEach(r => {
                    if (r.id !== root.id && !root.children.some(c => c.id === r.id)) {
                        root.children.push(r);
                    }
                });
            }

            this.orgTreeRoot = root;
        },

        isNodeMatchingSearch(node) {
            if (!this.searchQuery) return true;
            const q = this.searchQuery.toLowerCase();
            return (
                node.name.toLowerCase().includes(q) ||
                node.role.toLowerCase().includes(q) ||
                node.team_name.toLowerCase().includes(q) ||
                node.department_name.toLowerCase().includes(q)
            );
        },

        toggleNodeCollapse(nodeId) {
            this.collapsedNodes[nodeId] = !this.collapsedNodes[nodeId];
            if (window.lucide) setTimeout(lucide.createIcons, 50);
        },

        isNodeCollapsed(nodeId) {
            return !!this.collapsedNodes[nodeId];
        },

        expandAll() {
            this.collapsedNodes = {};
            if (window.lucide) setTimeout(lucide.createIcons, 50);
        },

        collapseAll() {
            const newCollapsed = {};
            this.orgChartNodes.forEach(n => {
                if (n.direct_reports_count > 0) newCollapsed[n.id] = true;
            });
            this.collapsedNodes = newCollapsed;
            if (window.lucide) setTimeout(lucide.createIcons, 50);
        },

        zoomIn() {
            if (this.zoomLevel < 1.6) this.zoomLevel = +(this.zoomLevel + 0.15).toFixed(2);
        },

        zoomOut() {
            if (this.zoomLevel > 0.5) this.zoomLevel = +(this.zoomLevel - 0.15).toFixed(2);
        },

        resetZoom() {
            this.zoomLevel = 1.0;
        },

        openReportingModal(node) {
            this.reportingForm = {
                user_id: node.id,
                user_name: node.name,
                current_manager_id: node.parent_id,
                new_manager_id: node.parent_id || ''
            };
            this.showReportingModal = true;
        },

        async saveReportingLine() {
            if (!this.reportingForm.user_id) return;
            try {
                const res = await fetch('/teams/api/update-reporting/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        user_id: this.reportingForm.user_id,
                        reporting_to_id: this.reportingForm.new_manager_id ? parseInt(this.reportingForm.new_manager_id) : null
                    })
                });
                const data = await res.json();
                if (res.ok && data.status === 'success') {
                    this.showToast(data.message, 'success');
                    this.showReportingModal = false;
                    await this.loadAllData();
                } else {
                    this.showToast(data.message || 'Failed to update reporting line.', 'error');
                }
            } catch (e) {
                this.showToast('Network error while updating reporting line.', 'error');
            }
        },

        showToast(msg, type = 'info') {
            this.toastMessage = msg;
            this.toastType = type;
            this.showToastNotification = true;
            setTimeout(() => {
                this.showToastNotification = false;
            }, 3500);
        }
    };
};
