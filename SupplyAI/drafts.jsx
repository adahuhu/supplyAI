// 采购计划创建页 — 对齐凌羿 ERP 的创建采购计划页面。

function ErpSelect({ value = '请选择', width = 180, muted = false }) {
  return (
    <button style={{
      width,
      height: 42,
      border: '1px solid #d9dee8',
      borderRadius: 4,
      background: '#fff',
      color: muted ? '#a6afbd' : '#203354',
      fontSize: 14,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 14px',
      fontFamily: 'inherit',
    }}>
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</span>
      <span style={{ color: '#b7bfcc', fontSize: 18 }}>⌄</span>
    </button>
  );
}

function ErpHeader() {
  const nav = ['工作台', '设置', '基础资料', '供应链', '财务', '亚马逊', 'Tiktok', '...'];
  return (
    <div style={{
      height: 58,
      background: '#fff',
      borderBottom: '1px solid #edf0f5',
      display: 'flex',
      alignItems: 'center',
      padding: '0 24px',
      gap: 28,
      color: '#243654',
      flex: 'none',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 190 }}>
        <div style={{
          width: 28,
          height: 28,
          borderRadius: 6,
          background: 'linear-gradient(135deg, #2f73ff, #8bb6ff)',
          transform: 'skew(-12deg)',
        }}/>
        <div style={{ fontSize: 26, color: '#176bff', fontWeight: 800, letterSpacing: .2 }}>凌羿ERP</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 28, flex: 1 }}>
        {nav.map((n, i) => (
          <div key={n} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 16, color: i === 0 ? '#1b2c4b' : '#4a5568', fontWeight: i === 0 ? 600 : 500 }}>
            <span style={{ width: 18, height: 18, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: '#515b6d' }}>
              {i === 0 ? <Icon name="columns" size={17}/> : i === 1 ? <Icon name="settings" size={17}/> : i === 2 ? <Icon name="list" size={17}/> : i === 3 ? <Icon name="truck" size={17}/> : i === 4 ? <Icon name="package" size={17}/> : <Icon name="box" size={17}/>}
            </span>
            <span>{n}</span>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 18, color: '#36437a' }}>
        <div style={{ minWidth: 150, height: 40, borderRadius: 6, background: '#f4f6fb', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontWeight: 600 }}>
          <span style={{ width: 20, height: 20, borderRadius: 5, background: '#4c8dff' }}/>
          凌羿ERP
          <Icon name="chevron-down" size={14}/>
        </div>
        <Icon name="search" size={22}/>
        <Icon name="bell" size={22}/>
        <span style={{ position: 'relative' }}>
          <Icon name="info" size={22}/>
          <span style={{ position: 'absolute', right: -8, top: -10, minWidth: 18, height: 18, borderRadius: 999, background: '#ff4d5a', color: '#fff', fontSize: 11, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>4</span>
        </span>
        <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#f2c6a6' }}/>
        <span style={{ fontSize: 14, fontWeight: 600 }}>胡仕玲</span>
      </div>
    </div>
  );
}

function ErpLeftRail() {
  return (
    <div style={{
      width: 76,
      background: '#fff',
      borderRight: '1px solid #edf0f5',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      paddingTop: 64,
      gap: 26,
      flex: 'none',
    }}>
      {['package', 'list', 'box', 'truck'].map((name) => (
        <div key={name} style={{ width: 30, height: 30, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#182b4a' }}>
          <Icon name={name} size={24} stroke={1.9}/>
        </div>
      ))}
      <div style={{ flex: 1 }}/>
      <div style={{ width: 32, height: 32, marginBottom: 20, background: '#f0f3f9', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#1b2c4b' }}>
        <Icon name="menu" size={20}/>
      </div>
    </div>
  );
}

function PurchasePlanRow({ sku, onRemove }) {
  const image = sku.image || `https://placehold.co/48x48/e8edf7/6b7890?text=${encodeURIComponent((sku.msku || 'SKU').slice(-3))}`;
  const purchaseQty = sku.purchaseQty ?? sku.suggestQty ?? '';
  return (
    <tr>
      <td style={{ width: 168 }}>
        <img src={image} style={{ width: 50, height: 50, borderRadius: 6, objectFit: 'cover' }}/>
      </td>
      <td style={{ width: 210 }}>
        <div style={{ color: '#1b68ff', fontSize: 15, fontWeight: 600, marginBottom: 6 }}>{sku.sku || sku.msku}</div>
        <div style={{ color: '#14264a', fontSize: 14, fontWeight: 600 }}>{sku.name || sku.msku}</div>
      </td>
      <td style={{ width: 210 }}><ErpSelect muted/></td>
      <td style={{ width: 220 }}><ErpSelect value={sku.supplier || '东莞市洪寿...'} width={182}/></td>
      <td style={{ width: 160 }}><span style={{ fontSize: 15, color: '#1d2f51', fontWeight: 600 }}>{sku.brand || '大s'}</span></td>
      <td style={{ width: 210 }}><ErpSelect value="请选择是否..." muted/></td>
      <td style={{ width: 210 }}><ErpSelect muted/></td>
      <td style={{ width: 220 }}><ErpSelect value="输入搜索" muted width={210}/></td>
      <td style={{ width: 190 }}>
        <input value={sku.msku || ''} readOnly style={{ width: 170, height: 42, border: '1px solid #d9dee8', borderRadius: 4, padding: '0 12px', color: '#203354', fontSize: 14 }}/>
      </td>
      <td style={{ width: 160 }}>
        <input defaultValue={purchaseQty} placeholder="0" style={{ width: 120, height: 42, border: '1px solid #d9dee8', borderRadius: 4, padding: '0 12px', color: '#203354', fontSize: 14 }}/>
      </td>
      <td style={{ width: 160 }}><ErpSelect value="请选择" muted width={140}/></td>
      <td style={{ width: 110, textAlign: 'center', color: '#ff3d18', fontSize: 15, fontWeight: 500 }}>
        <button onClick={onRemove} style={{ border: 0, background: 'transparent', color: '#ff3d18', cursor: 'pointer', fontSize: 15 }}>移除</button>
      </td>
    </tr>
  );
}

function DraftsPage({ setRoute, showToast, initialIds = [], initialItems = [] }) {
  const initialSelected = React.useMemo(() => {
    const requested = initialItems.length
      ? initialItems
      : (initialIds || []).map(id => ({ id }));
    const itemMap = new Map(requested.map(it => [String(it.id), it]));
    const picked = requested
      .map(it => (window.SKUS || []).find(s => String(s.id) === String(it.id)))
      .filter(Boolean);
    if (picked.length) {
      return picked.map(s => {
        const extra = itemMap.get(String(s.id)) || {};
        return {
          ...s,
          purchaseQty: extra.qty ?? extra.purchaseQty ?? s.suggestQty,
          supplier: extra.supplier || s.supplier,
        };
      });
    }
    return (window.SKUS || []).filter(s => s.suggest).slice(0, 1).map(s => ({ ...s, purchaseQty: s.suggestQty }));
  }, [initialIds.join('|'), JSON.stringify(initialItems), (window.SKUS || []).length]);
  const [rows, setRows] = React.useState(initialSelected);

  React.useEffect(() => {
    setRows(initialSelected);
  }, [initialSelected]);

  const selectedCount = rows.length;
  const totalQty = rows.reduce((sum, s) => sum + Number(s.purchaseQty ?? s.suggestQty ?? 0), 0);
  const th = {
    height: 78,
    padding: '0 14px',
    textAlign: 'left',
    color: '#172b52',
    fontSize: 15,
    fontWeight: 700,
    borderBottom: '1px solid #e8edf5',
    whiteSpace: 'nowrap',
    background: '#fff',
  };

  return (
    <div style={{
      minHeight: '100%',
      background: '#f4f6fa',
      color: '#172b52',
      fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    }}>
        <main style={{ minWidth: 0, padding: '0 22px 24px' }}>
          <div style={{ height: 62, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'flex-end', height: '100%' }}>
              {['首页', '采购计划', '创建采购计划'].map((tab, i) => (
                <button key={tab} onClick={() => i === 0 && setRoute && setRoute({ page: 'dashboard' })} style={{
                  minWidth: i === 2 ? 176 : 110,
                  height: i === 2 ? 50 : 48,
                  border: 0,
                  borderTopLeftRadius: i === 2 ? 10 : 0,
                  borderTopRightRadius: i === 2 ? 10 : 0,
                  background: i === 2 ? '#fff' : '#f0f2f7',
                  color: i === 2 ? '#1269ff' : '#172b52',
                  fontSize: 16,
                  fontWeight: i === 2 ? 700 : 600,
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}>{tab}</button>
              ))}
            </div>
            <button style={{ border: 0, background: 'transparent', color: '#173157', cursor: 'pointer' }}>
              <Icon name="refresh" size={20}/>
            </button>
          </div>

          <section style={{ background: '#fff', borderRadius: 4, boxShadow: '0 1px 2px rgba(16,24,40,.04)', minHeight: 'calc(100vh - 160px)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ height: 68, display: 'flex', alignItems: 'center', padding: '0 12px', borderBottom: '1px solid #e8edf5' }}>
              <div style={{ fontSize: 19, fontWeight: 800, color: '#14264a' }}>创建采购计划</div>
            </div>

            <div style={{ height: 90, display: 'flex', alignItems: 'center', gap: 10, padding: '0 22px', borderBottom: '1px solid #e8edf5' }}>
              <button style={{ height: 42, minWidth: 84, border: '1px solid #1469ff', borderRadius: 4, background: '#fff', color: '#1167ff', fontSize: 16, fontWeight: 700 }}>添加</button>
              <button style={{ height: 42, minWidth: 84, border: '1px solid #1469ff', borderRadius: 4, background: '#fff', color: '#1167ff', fontSize: 16, fontWeight: 700 }}>导入</button>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#172b52', marginLeft: 2 }}>
                已选择 {selectedCount}个产品，共计采购数量 {totalQty}个
              </div>
              <button style={{ height: 44, minWidth: 104, border: '1px solid #d2d8e3', borderRadius: 4, background: '#fff', color: '#172b52', fontSize: 16, fontWeight: 700, marginLeft: 12 }}>批量填写</button>
              <div style={{ flex: 1 }}/>
              <label style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 16, fontWeight: 700, color: '#172b52' }}>
                <span style={{ width: 20, height: 20, border: '1px solid #d2d8e3', borderRadius: 4, display: 'inline-block' }}/>
                1688配对检查
                <Icon name="info" size={16} color="#9aa4b5"/>
              </label>
            </div>

            <div style={{ padding: '24px 22px 0', flex: 1, minHeight: 0 }}>
              <div style={{ border: '1px solid #e1e6ef', borderRadius: 5, overflow: 'auto', height: 'calc(100vh - 360px)', minHeight: 500, background: '#fff' }}>
                <table style={{ borderCollapse: 'collapse', minWidth: 2020, width: '100%' }}>
                  <thead>
                    <tr>
                      <th style={{ ...th, width: 168 }}>图片</th>
                      <th style={{ ...th, width: 210 }}>SKU/品名 <Icon name="sort" size={13} color="#b0bac8"/></th>
                      <th style={{ ...th, width: 210 }}><span style={{ color: '#f23d3d' }}>*</span> 仓库 <span style={{ color: '#1269ff', marginLeft: 12, fontWeight: 600 }}>批量</span></th>
                      <th style={{ ...th, width: 220 }}>供应商 <span style={{ display: 'inline-block', width: 20, height: 20, border: '1px solid #d2d8e3', borderRadius: 4, verticalAlign: 'middle', marginLeft: 8 }}/> <span style={{ color: '#1269ff', marginLeft: 18, fontWeight: 600 }}>批量</span></th>
                      <th style={{ ...th, width: 160 }}>品牌</th>
                      <th style={{ ...th, width: 210 }}>加急 <span style={{ color: '#1269ff', marginLeft: 12, fontWeight: 600 }}>批量</span></th>
                      <th style={{ ...th, width: 210 }}>店铺 <span style={{ color: '#1269ff', marginLeft: 12, fontWeight: 600 }}>批量</span> <Icon name="sort" size={13} color="#b0bac8"/></th>
                      <th style={{ ...th, width: 220 }}>FNSKU <span style={{ color: '#1269ff', marginLeft: 12, fontWeight: 600 }}>调整</span></th>
                      <th style={{ ...th, width: 190 }}>MSKU <Icon name="sort" size={13} color="#b0bac8"/></th>
                      <th style={{ ...th, width: 160 }}>采购数量</th>
                      <th style={{ ...th, width: 160 }}>预计到货</th>
                      <th style={{ ...th, width: 110, textAlign: 'center' }}><Icon name="columns" size={20} color="#173157"/></th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((sku) => (
                      <PurchasePlanRow key={sku.id} sku={sku} onRemove={() => setRows(prev => prev.filter(x => x.id !== sku.id))}/>
                    ))}
                    {rows.length === 0 && (
                      <tr>
                        <td colSpan={12} style={{ height: 220, textAlign: 'center', color: '#8a95a8', fontSize: 15 }}>
                          暂无产品，请点击“添加”选择需要生成采购计划的 SKU。
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
                <div style={{ height: 66, borderTop: '1px solid #e8edf5', display: 'flex', alignItems: 'center', padding: '0 14px', fontSize: 16, fontWeight: 800, color: '#14264a' }}>
                  合计
                </div>
              </div>
            </div>

            <div style={{ height: 74, borderTop: '1px solid #e8edf5', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 16, padding: '0 22px', background: '#fff' }}>
              <button onClick={() => setRoute && setRoute({ page: 'dashboard' })} style={{ width: 110, height: 42, border: '1px solid #d2d8e3', borderRadius: 4, background: '#fff', color: '#172b52', fontSize: 16, fontWeight: 700 }}>取消</button>
              <button onClick={() => showToast && showToast('采购计划已暂存')} style={{ width: 110, height: 42, border: '1px solid #d2d8e3', borderRadius: 4, background: '#fff', color: '#172b52', fontSize: 16, fontWeight: 700 }}>暂存</button>
              <button onClick={() => showToast && showToast('采购计划已提交')} style={{ width: 112, height: 42, border: 0, borderRadius: 4, background: '#1469ff', color: '#fff', fontSize: 16, fontWeight: 800 }}>提交</button>
            </div>
          </section>
        </main>
    </div>
  );
}

Object.assign(window, { DraftsPage });
