/* ===== DocScanX - App Logic (API-wired) ===== */
const { createApp, ref, computed, onMounted, watch, nextTick } = Vue;

createApp({
  setup() {
    const BASE = '/api/v1';

    // ---- Helpers ----
    async function api(path, opts = {}) {
      const res = await fetch(BASE + path, opts);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      return res.json();
    }

    // ---- Toast notifications ----
    const toasts = ref([]);
    var _toastId = 0;
    function showToast(msg, type) {
      type = type || 'info';
      var id = ++_toastId;
      toasts.value.push({id: id, msg: msg, type: type});
      setTimeout(function() {
        toasts.value = toasts.value.filter(function(t) { return t.id !== id; });
      }, 3500);
    }
    function removeToast(id) {
      toasts.value = toasts.value.filter(function(t) { return t.id !== id; });
    }

    // ---- Topbar ----
    const currentTab = ref('dashboard');
    const tabs = ref([
      { id:'dashboard', label:'工作台', icon:'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>' },
      { id:'tasks', label:'扫描任务', icon:'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>' },
      { id:'persons', label:'数据主体', icon:'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>' },
      { id:'settings', label:'系统配置', icon:'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>' },
      { id:'logs', label:'系统日志', icon:'<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>' }
    ]);
    const moduleName = computed(() => {
      const t = tabs.value.find(t => t.id === currentTab.value);
      return t ? t.label : '';
    });
    const modelReady = ref(false);

    const folderSvg = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>';
    const fileSvg = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>';

    // ---- Dashboard ----
    const stats = ref([
      { label:'总任务', value:0, bg:'#4f6ef7', icon:'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>' },
      { label:'总文件', value:0, bg:'#22c55e', icon:'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>' },
      { label:'主体', value:0, bg:'#f59e0b', icon:'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>' },
      { label:'敏感项', value:0, bg:'#ef4444', icon:'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#fff" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>' }
    ]);

    const quickScanResult = ref(null);
    const quickScanLoading = ref(false);

    async function quickScanFile(e) {
      var file = e.target.files[0];
      if (!file) return;
      quickScanLoading.value = true;
      quickScanResult.value = null;
      try {
        var form = new FormData();
        form.append('file', file);
        var upRes = await fetch(BASE + '/scan/upload', {method: 'POST', body: form});
        if (!upRes.ok) {
          var errText = await upRes.text();
          try { var errJson = JSON.parse(errText); errText = errJson.detail || errJson.message || errText; } catch (_) {}
          showToast('上传失败: ' + errText, 'error');
          quickScanLoading.value = false;
          return;
        }
        var upData = await upRes.json();
        if (upData.code !== 0) {
          showToast('上传失败: ' + (upData.message || JSON.stringify(upData)), 'error');
          quickScanLoading.value = false;
          return;
        }
        var serverPath = upData.data.path;
        var scanRes = await api('/scan/start', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({path: serverPath, name: file.name})
        });
        if (scanRes.code !== 0) { showToast('扫描失败: ' + scanRes.message, 'error'); quickScanLoading.value = false; return; }
        var detailRes = await api('/reports/' + scanRes.data.report_id);
        if (detailRes.code === 0) {
          var d = detailRes.data;
          var entities = [];
          (d.files || []).forEach(function(f) {
            (f.entities || []).forEach(function(e) {
              var c = e.confidence;
              var cf = (typeof c === 'number') ? Math.round(c * 100) + '%' : (c || '-');
              entities.push({type: e.type, val: e.value, conf: cf});
            });
          });
          quickScanResult.value = {file: serverPath, items: entities};
        }
        await loadAllReports();
        showToast('扫描完成', 'success');
      } catch (e) {
        showToast('请求失败: ' + (e.message || String(e)), 'error');
      } finally {
        quickScanLoading.value = false;
      }
    }

    const recentTasks = ref([]);

    // ---- Tasks ----
    const showWizard = ref(false);
    const wizardStep = ref(1);
    const remoteTesting = ref(false);
    const taskView = ref('list');
    const wizardData = ref({ type:'file', name:'', path:'', uploadName:'', uploadSize:0, subdir:true, unzip:true, mask:true, threshold:0.75,
      remote: { host:'', port:21, username:'', password:'', base_path:'/' },
      remoteTestResult: null,
      fileTypes: {
        office: { checked: true, label: '文档',
          exts: { docx: true, xlsx: true, pptx: true, pdf: true, doc: false, xls: false, ppt: false }},
        image: { checked: true, label: '图片',
          exts: { jpg: true, jpeg: true, png: true, bmp: true, tiff: true }},
        text: { checked: true, label: '文本',
          exts: { txt: true, csv: true, json: true, xml: true, md: true, log: true }},
        archive: { checked: true, label: '压缩包',
          exts: { zip: true, rar: true, '7z': true }}
      }
    });
    const taskFilter = ref({ status:'', search:'' });
    const allTasks = ref([]);

    const filteredTasks = computed(() => {
      let list = allTasks.value;
      if (taskFilter.value.status) list = list.filter(t => t.status === taskFilter.value.status);
      if (taskFilter.value.search) list = list.filter(t => t.name.includes(taskFilter.value.search));
      return list;
    });

    const selectedTaskFile = ref(null);
    const taskFileDetails = ref([]);

    async function viewFileDetail(task) {
      selectedTaskFile.value = task;
      taskFileDetails.value = [];
      try {
        const res = await api('/reports/' + task.id);
        if (res.code === 0) {
          const files = res.data.files || [];
          taskFileDetails.value = files.map(f => ({
            file: f.path,
            status: f.error ? '失败' : '成功',
            items: (f.entities || []).reduce((acc, e) => {
              const found = acc.find(x => x.type === e.type);
              found ? found.count++ : acc.push({type: e.type, count: 1});
              return acc;
            }, []),
            persons: f.persons || 0
          }));
        }
      } catch (e) {
        console.error('加载文件详情失败:', e);
      }
    }

    function viewReport(task) {
      selectedTaskFile.value = null;
      selectedReportTask.value = task.id;
      taskView.value = 'report';
    }

    function backToTaskList() {
      taskView.value = 'list';
    }

    // ---- Folder browser ----
    async function browseFolder() {
      try {
        var res = await api('/scan/browse-folder', {method: 'POST'});
        if (res.code === 0 && res.data.path) {
          wizardData.value.path = res.data.path;
        } else if (res.code !== 0) {
          showToast(res.message || '无法打开文件夹选择器，请手动输入路径', 'info');
        }
      } catch (e) {
        showToast('文件夹选择失败，请手动输入路径', 'info');
      }
    }

    async function testRemoteConnection() {
      var r = wizardData.value.remote;
      if (!r.host) { showToast('请输入服务器地址', 'error'); return; }
      remoteTesting.value = true;
      wizardData.value.remoteTestResult = null;
      try {
        var res = await api('/remote/test', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            host: r.host, port: r.port,
            username: r.username, password: r.password,
            base_path: r.base_path
          })
        });
        if (res.code === 0) {
          wizardData.value.remoteTestResult = {success: true, msg: res.data.message};
          showToast(res.data.message, 'success');
        } else {
          wizardData.value.remoteTestResult = {success: false, msg: res.message};
          showToast(res.message, 'error');
        }
      } catch (e) {
        wizardData.value.remoteTestResult = {success: false, msg: '连接失败: ' + (e.message || String(e))};
        showToast('连接失败: ' + (e.message || String(e)), 'error');
      } finally {
        remoteTesting.value = false;
      }
    }

    const anomalousFiles = computed(() => {
      if (!reportDetail.value) return [];
      return (reportDetail.value.files || [])
        .filter(function(f) { return f.error; })
        .map(function(f) {
          var etype = f.error || '';
          if (etype.includes('加密') || etype.includes('password')) return {path: f.path, type: '加密文件'};
          if (etype.includes('解析') || etype.includes('parse')) return {path: f.path, type: '解析失败'};
          return {path: f.path, type: '解析失败'};
        });
    });

    function downloadAnomalousList() {
      var lines = anomalousFiles.value.map(function(f) { return f.path + '\t' + f.type; });
      var header = '文件路径\t异常类型\n';
      var blob = new Blob([header + lines.join('\n')], { type:'text/csv;charset=utf-8;' });
      var link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = '异常文件清单.csv';
      link.click();
      URL.revokeObjectURL(link.href);
    }

    function exportReport(type) {
      if (!selectedReportTask.value) return;
      var url = BASE + '/reports/' + selectedReportTask.value + '/export?format=' + type;
      window.open(url, '_blank');
    }

    const selectedReportTask = ref('');
    const reportDetail = ref(null);
    const entityLabels = {name:'姓名', id_card:'身份证', phone:'手机', email:'邮箱', bank_card:'银行卡', address:'地址', wechat:'微信', birthday:'生日', job_no:'工号', passport:'护照', plate_no:'车牌', gender:'性别'};
    function entityLabel(type) { return entityLabels[type] || type; }
    function fileBasename(path) { return (path || '').replace(/\\/g, '/').split('/').pop(); }

    const reportStats = ref([
      { label:'已处理', value:0, bg:'#4f6ef7' },
      { label:'涉及主体', value:0, bg:'#f59e0b' },
      { label:'敏感字段', value:0, bg:'#ef4444' },
      { label:'异常文件', value:0, bg:'#94a3b8' }
    ]);

    const riskDistribution = computed(function() {
      if (!reportDetail.value || !reportDetail.value.summary) return [];
      var rd = reportDetail.value.summary.risk_distribution;
      if (!rd) return [];
      var total = (rd.critical||0) + (rd.high||0) + (rd.medium||0) + (rd.low||0);
      if (total === 0) return [];
      return [
        {label: '极高风险', level: 'critical', count: rd.critical||0, pct: Math.round((rd.critical||0)/total*100)},
        {label: '高风险', level: 'high', count: rd.high||0, pct: Math.round((rd.high||0)/total*100)},
        {label: '中风险', level: 'medium', count: rd.medium||0, pct: Math.round((rd.medium||0)/total*100)},
        {label: '低风险', level: 'low', count: rd.low||0, pct: Math.round((rd.low||0)/total*100)}
      ];
    });

    const reportProgress = ref(null);

    function _fileTypesToExtGroups(ft) {
      var extToGroup = {
        docx: 'office_new', xlsx: 'office_new', pptx: 'office_new',
        pdf: 'pdf', doc: 'office_old', xls: 'office_old', ppt: 'office_old',
        jpg: 'image', jpeg: 'image', png: 'image', bmp: 'image', tiff: 'image',
        txt: 'text', csv: 'text', md: 'text', log: 'text',
        json: 'structured', xml: 'structured',
        zip: 'archive', rar: 'archive', '7z': 'archive'
      };
      var groups = {};
      Object.keys(ft).forEach(function(cat) {
        if (ft[cat].checked) {
          Object.keys(ft[cat].exts).forEach(function(ext) {
            if (ft[cat].exts[ext] && extToGroup[ext]) {
              groups[extToGroup[ext]] = true;
            }
          });
        }
      });
      return groups;
    }

    async function onFileSelected(e) {
      var file = e.target.files[0];
      if (!file) return;
      wizardData.value.uploadName = file.name;
      wizardData.value.uploadSize = (file.size / (1024*1024)).toFixed(2);
      var form = new FormData();
      form.append('file', file);
      try {
        var res = await fetch(BASE + '/scan/upload', {method: 'POST', body: form});
        if (!res.ok) {
          var errText = await res.text();
          try { var errJson = JSON.parse(errText); errText = errJson.detail || errJson.message || errText; } catch (_) {}
          showToast('上传失败: ' + errText, 'error');
          return;
        }
        var data = await res.json();
        if (data.code === 0) {
          wizardData.value.path = data.data.path;
        } else {
          showToast('上传失败: ' + (data.message || JSON.stringify(data)), 'error');
        }
      } catch (err) {
        showToast('上传失败: ' + (err.message || String(err)), 'error');
      }
    }

    async function startTask() {
      const d = wizardData.value;
      if (d.type === 'remote') {
        if (!d.remote.host) { showToast('请输入服务器地址', 'error'); return; }
      } else {
        if (!d.path) { showToast('请选择文件或输入目标路径', 'error'); return; }
      }
      showWizard.value = false;

      var isRemote = d.type === 'remote';
      var endpoint = isRemote ? '/remote/scan' : '/scan/start';
      var payload = isRemote ? {
        host: d.remote.host,
        port: d.remote.port,
        username: d.remote.username,
        password: d.remote.password,
        base_path: d.remote.base_path,
        name: d.name,
        mask_enabled: d.mask,
        ext_groups: _fileTypesToExtGroups(d.fileTypes)
      } : {
        path: d.path,
        name: d.name,
        include_subdir: d.subdir,
        extract_archive: d.unzip,
        mask_enabled: d.mask,
        ext_groups: _fileTypesToExtGroups(d.fileTypes)
      };

      try {
        const res = await api(endpoint, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload)
        });
        if (res.code !== 0) { showToast('扫描启动失败: ' + res.message, 'error'); return; }

        const taskId = res.data.task_id;
        showToast('扫描任务已启动', 'success');

        const poll = setInterval(async () => {
          try {
            const s = await api('/scan/status/' + taskId);
            if (s.code === 0) {
              if (s.data.status === 'done') {
                clearInterval(poll);
                await loadAllReports();
                showToast('扫描完成: ' + s.data.total_files + ' 文件, ' + s.data.total_persons + ' 人', 'success');
              } else if (s.data.status === 'error') {
                clearInterval(poll);
                showToast('扫描失败: ' + (s.data.error || '未知错误'), 'error');
              }
            }
          } catch (e) { /* polling retry */ }
        }, 1000);
      } catch (e) {
        showToast('请求失败: ' + e.message, 'error');
      }
    }

    async function loadReportDetail(reportId) {
      if (!reportId) return;
      try {
        const res = await api('/reports/' + reportId);
        if (res.code === 0) {
          reportDetail.value = res.data;
          const files = res.data.files || [];
          const summary = res.data.summary || {};
          reportStats.value = [
            { label:'已处理', value: files.length, bg:'#4f6ef7' },
            { label:'涉及主体', value: summary.total_persons || 0, bg:'#f59e0b' },
            { label:'敏感字段', value: files.reduce((s,f) => s + (f.entities||[]).length, 0), bg:'#ef4444' },
            { label:'异常文件', value: files.filter(f=>f.error).length, bg:'#94a3b8' }
          ];
          taskFileDetails.value = files.map(f => ({
            file: f.path, status: f.error ? '失败' : '成功',
            items: (f.entities || []).reduce((acc, e) => {
              const found = acc.find(x => x.type === e.type);
              found ? found.count++ : acc.push({type: e.type, count: 1});
              return acc;
            }, []),
            persons: f.persons || 0
          }));
          loadFileTraces(reportId);
        }
      } catch (e) {
        console.error('加载报告详情失败:', e);
      }
    }

    watch(selectedReportTask, (newId) => {
      if (newId) loadReportDetail(newId);
    });

    // ---- Persons ----
    const personFilter = ref({ risk:'', search:'' });
    const persons = ref([]);
    const personPage = ref(1);
    const personTotal = ref(0);
    const personPerPage = ref(50);

    const filteredPersons = computed(() => {
      let list = persons.value;
      if (personFilter.value.risk) list = list.filter(p => p.risk === personFilter.value.risk);
      if (personFilter.value.search) list = list.filter(p => (p.name||'').includes(personFilter.value.search)
        || (p.id_card||'').includes(personFilter.value.search));
      return list;
    });

    const selectedPerson = ref(null);
    const personRelatedFiles = ref([]);
    const personRelatedLoading = ref(false);

    async function showPersonDetail(p) {
      selectedPerson.value = p;
      personRelatedFiles.value = [];
      personRelatedLoading.value = true;

      var rids = p.report_ids || [];
      if (rids.length === 0 && p.report_id) rids = [p.report_id];

      for (var i = 0; i < rids.length; i++) {
        try {
          var res = await api('/reports/' + rids[i]);
          if (res.code === 0) {
            // find report display name
            var task = allTasks.value.find(function(t) { return t.id === rids[i]; });
            var reportName = task ? task.name : rids[i];

            (res.data.files || []).forEach(function(f) {
              var matchCount = (f.entities || []).filter(function(e) {
                return (e.type === 'name' && e.value === p.name) ||
                       (p.id_card && e.value === p.id_card) ||
                       (p.phone && e.value === p.phone) ||
                       (p.email && e.value === p.email);
              }).length;
              if (matchCount > 0) {
                personRelatedFiles.value.push({
                  path: f.path,
                  isDir: false,
                  fields: matchCount,
                  report: reportName
                });
              }
            });
          }
        } catch (e) { console.error('加载关联文件失败:', e); }
      }

      // if no matching files found, show all report IDs
      if (personRelatedFiles.value.length === 0 && rids.length > 0) {
        rids.forEach(function(rid) {
          var task = allTasks.value.find(function(t) { return t.id === rid; });
          personRelatedFiles.value.push({
            path: task ? task.name : rid,
            isDir: true,
            fields: 0,
            report: task ? task.name : rid
          });
        });
      }

      personRelatedLoading.value = false;
    }

    function closePersonDetail() { selectedPerson.value = null; }

    const personSensitiveFields = computed(() => {
      if (!selectedPerson.value) return [];
      const map = {name:'姓名', id_card:'身份证号', phone:'手机号码', bank_card:'银行卡号',
        address:'家庭地址', email:'电子邮箱', wechat:'微信', birthday:'生日',
        job_no:'工号', passport:'护照号', plate_no:'车牌号', gender:'性别'};
      return Object.keys(map).filter(k => selectedPerson.value[k]).map(k => ({
        field: map[k], count: 1
      }));
    });

    // ---- Settings ----
    const settings = ref({
      mask:true, threshold:0.75, ocr:'RapidOCR', concurrency:4,
      memory:'2048', modelPath:'./models', logLevel:'INFO',
      maxFileSize:50, timeout:300, tempDir:'./temp'
    });

    const settingsLoaded = ref(false);

    function configToSettings(cfg) {
      return {
        mask: cfg.inference?.mask_enabled ?? true,
        threshold: cfg.inference?.confidence_threshold ?? 0.75,
        ocr: cfg.model?.ocr?.engine === 'rapidocr' ? 'RapidOCR' : (cfg.model?.ocr?.engine || 'RapidOCR'),
        concurrency: cfg.concurrency?.file_parse_workers ?? 4,
        memory: String(cfg.memory?.max_memory_mb ?? 2048),
        modelPath: cfg.path?.model_dir || './models',
        logLevel: cfg.log?.level || 'INFO',
        maxFileSize: cfg.scan?.max_file_size_mb ?? 50,
        timeout: cfg.task?.file_timeout ?? 300,
        tempDir: cfg.path?.temp_dir || './temp'
      };
    }

    function settingsToConfig(s) {
      return {
        inference: {mask_enabled: s.mask, confidence_threshold: Number(s.threshold)},
        model: {ocr: {engine: s.ocr === 'RapidOCR' ? 'rapidocr' : s.ocr.toLowerCase()}},
        concurrency: {file_parse_workers: Number(s.concurrency)},
        memory: {max_memory_mb: Number(s.memory)},
        path: {model_dir: s.modelPath, temp_dir: s.tempDir},
        log: {level: s.logLevel},
        scan: {max_file_size_mb: Number(s.maxFileSize)},
        task: {file_timeout: Number(s.timeout)}
      };
    }

    async function resetSettings() {
      try {
        const res = await api('/config/defaults');
        if (res.code === 0) {
          settings.value = configToSettings(res.data);
          showToast('已恢复默认配置', 'success');
        }
      } catch (e) {
        showToast('加载默认配置失败', 'error');
      }
    }

    async function saveSettings() {
      try {
        const body = settingsToConfig(settings.value);
        const res = await api('/config', {
          method: 'PUT',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(body)
        });
        if (res.code === 0) {
          showToast('配置已保存', 'success');
        } else {
          showToast('保存失败: ' + res.message, 'error');
        }
      } catch (e) {
        showToast('保存失败: ' + e.message, 'error');
      }
    }

    // ---- Logs ----
    const logFilter = ref({ level:'', search:'' });
    const logView = ref('audit');
    const auditLogs = ref([]);
    const filteredAuditLogs = computed(function() {
      var list = auditLogs.value;
      if (logFilter.value.level) list = list.filter(function(l) {
        return l.result === '失败' ? 'ERROR' === logFilter.value.level : 'INFO' === logFilter.value.level;
      });
      if (logFilter.value.search) {
        var q = logFilter.value.search.toLowerCase();
        list = list.filter(function(l) { return (l.action||'').toLowerCase().includes(q); });
      }
      return list;
    });
    const taskSensitiveTotal = computed(function() {
      return taskFileDetails.value.reduce(function(s, fd) {
        return s + fd.items.reduce(function(t, i) { return t + i.count; }, 0);
      }, 0);
    });

    const fileTraces = ref([]);
    const traceReportId = ref('');

    watch(traceReportId, function(newId) {
      loadFileTraces(newId);
    });

    async function loadAuditLogs() {
      try {
        var res = await api('/logs/files');
        var logFiles = (res.code === 0 && res.data) ? res.data : [];
        var auditFile = logFiles.find(function(f) { return f === 'audit.log'; });

        if (!auditFile) {
          // no audit log file yet — try direct query anyway
          res = await api('/logs?file=audit.log&page=1&page_size=50');
        } else {
          res = await api('/logs?file=audit.log&page=1&page_size=50');
        }

        if (res.code === 0) {
          auditLogs.value = (res.data.items || []).map(function(l) { return {
            time: l.time || '',
            action: l.message || '',
            result: (l.level === 'ERROR') ? '失败' : '成功'
          }; });
        }
      } catch (e) {
        console.error('加载审计日志失败:', e);
      }
    }

    async function loadFileTraces(reportId) {
      if (!reportId) { fileTraces.value = []; return; }
      try {
        const res = await api('/logs/trace?report_id=' + encodeURIComponent(reportId));
        if (res.code === 0) {
          fileTraces.value = (res.data.traces || []).map(t => ({
            path: (t.path||'').split('/').pop() || t.path,
            stage: t.stage,
            status: t.status === 'ok' ? '成功' : (t.status === 'error' ? '失败' : t.status),
            fields: t.fields || '-',
            error: t.error || ''
          }));
        }
      } catch (e) {
        console.error('加载文件轨迹失败:', e);
      }
    }

    // ---- Data loading ----
    async function loadAllReports() {
      try {
        const res = await api('/reports');
        if (res.code === 0) {
          const reports = res.data.reports || [];
          const completed = reports.map(r => ({
            id: r.id,
            name: r.name || r.id,
            type: '扫描任务',
            files: r.total_files,
            persons: r.total_persons,
            status: '已完成',
            progress: 100,
            time: r.generated_at
          }));
          allTasks.value = completed;
          var dayAgo = new Date(Date.now() - 24*60*60*1000);
          recentTasks.value = reports.filter(function(r) {
            var d = new Date(r.generated_at);
            return !isNaN(d.getTime()) && d >= dayAgo;
          }).slice(0, 5).map(function(r) {
            return {id: r.id, name: r.name || r.id, files: r.total_files, status: '已完成', time: r.generated_at};
          });
          let totalFiles = 0, totalPersons = 0, totalEntities = 0;
          reports.forEach(r => {
            totalFiles += r.total_files || 0;
            totalPersons += r.total_persons || 0;
            totalEntities += r.total_entities || 0;
          });
          stats.value = [
            { label:'总任务', value: reports.length, bg:'#4f6ef7', icon: stats.value[0].icon },
            { label:'总文件', value: totalFiles, bg:'#22c55e', icon: stats.value[1].icon },
            { label:'主体', value: totalPersons, bg:'#f59e0b', icon: stats.value[2].icon },
            { label:'敏感项', value: totalEntities, bg:'#ef4444', icon: stats.value[3].icon }
          ];
          if (!selectedReportTask.value && completed.length > 0) {
            selectedReportTask.value = completed[0].id;
          }
        }
      } catch (e) {
        console.error('加载报告列表失败:', e);
      }
    }

    async function loadPersons(page) {
      var pg = page || 1;
      try {
        var res = await api('/subjects?per_page=' + personPerPage.value + '&page=' + pg);
        if (res.code === 0) {
          personPage.value = res.data.page || pg;
          personTotal.value = res.data.total || 0;
          var raw = res.data.persons || [];
          var nameCount = {};
          var nameReports = {};
          raw.forEach(function(p) {
            var n = p.name || '';
            if (n) {
              nameCount[n] = (nameCount[n] || 0) + 1;
              if (!nameReports[n]) nameReports[n] = [];
              if (p.report_id && nameReports[n].indexOf(p.report_id) === -1) {
                nameReports[n].push(p.report_id);
              }
            }
          });
          persons.value = raw.map(function(p) {
            var n = p.name || '';
            return {
              name: n,
              id: p.id_card || '',
              id_card: p.id_card || '',
              phone: p.phone || '',
              address: p.address || '',
              email: p.email || '',
              bank_card: p.bank_card || '',
              wechat: p.wechat || '',
              birthday: p.birthday || '',
              job_no: p.job_no || '',
              passport: p.passport || '',
              plate_no: p.plate_no || '',
              gender: p.gender || '',
              risk: p.risk || '低',
              riskLevel: p.risk_level || 'low',
              confidence: p.confidence || '',
              report_id: p.report_id || '',
              report_ids: nameReports[n] || [],
              files: nameCount[n] || 1
            };
          });
        }
      } catch (e) {
        console.error('加载主体数据失败:', e);
      }
    }

    async function loadSettings() {
      try {
        const res = await api('/config');
        if (res.code === 0 && res.data && Object.keys(res.data).length > 0) {
          settings.value = configToSettings(res.data);
        }
        settingsLoaded.value = true;
      } catch (e) {
        console.error('加载配置失败:', e);
        settingsLoaded.value = true;
      }
    }

    async function checkHealth() {
      try {
        const res = await api('/health');
        if (res.code === 0) {
          modelReady.value = res.data.models_ready;
        }
      } catch (e) { /* offline */ }
    }

    // ---- Wizard helpers ----
    function openWizard(type) {
      wizardData.value.type = type;
      wizardData.value.name = '';
      wizardData.value.path = '';
      wizardData.value.uploadName = '';
      wizardData.value.uploadSize = 0;
      wizardData.value.remote = { host:'', port:21, username:'', password:'', base_path:'/' };
      wizardData.value.remoteTestResult = null;
      wizardStep.value = 1;
      showWizard.value = true;
    }

    function wizardNext() {
      if (wizardData.value.type === 'file') {
        wizardStep.value = wizardStep.value === 1 ? 3 : 3;
      } else {
        if (wizardStep.value < 3) wizardStep.value++;
      }
    }

    function wizardPrev() {
      if (wizardData.value.type === 'file') {
        wizardStep.value = wizardStep.value === 3 ? 1 : 1;
      } else {
        if (wizardStep.value > 1) wizardStep.value--;
      }
    }

    onMounted(async () => {
      await Promise.all([
        checkHealth(),
        loadAllReports(),
        loadPersons(),
        loadSettings()
      ]);
      await loadAuditLogs();
    });

    // Watch report tab to load detail
    return {
      currentTab, tabs, moduleName, modelReady,
      toasts, showToast, removeToast,
      folderSvg, fileSvg,
      stats, quickScanResult, quickScanLoading, quickScanFile, recentTasks,
      showWizard, wizardStep, wizardData, remoteTesting, taskView, openWizard, wizardNext, wizardPrev,
      onFileSelected, browseFolder, testRemoteConnection, backToTaskList, taskFilter, allTasks, filteredTasks,
      selectedTaskFile, taskFileDetails, taskSensitiveTotal, viewFileDetail, viewReport,
      anomalousFiles, downloadAnomalousList, exportReport,
      selectedReportTask, reportStats, reportProgress, reportDetail, riskDistribution, entityLabels, entityLabel, fileBasename, startTask,
      personFilter, persons, personPage, personTotal, personPerPage, filteredPersons, loadPersons,
      selectedPerson, showPersonDetail, closePersonDetail, personSensitiveFields, personRelatedFiles, personRelatedLoading,
      settings, resetSettings, saveSettings,
      logFilter, logView, auditLogs, filteredAuditLogs, fileTraces, traceReportId, loadFileTraces
    };
  }
}).mount('#app');
