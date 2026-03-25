/**
 * 5GInvest - PWA Frontend
 * Application mobile pour l'investissement guidé.
 */

const API = '';

// ─── Navigation ──────────────────────────────────────────

function showPage(name, ev) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav__item').forEach(n => {
    n.classList.remove('active');
    n.removeAttribute('aria-current');
  });
  const page = document.getElementById(`page-${name}`);
  if (page) page.classList.add('active');

  // Highlight nav item if triggered by nav button
  const target = ev?.currentTarget || (event && event.currentTarget);
  if (target && target.classList.contains('nav__item')) {
    target.classList.add('active');
    target.setAttribute('aria-current', 'page');
  }

  // Scroll to top
  window.scrollTo(0, 0);

  // Load page data
  const loaders = {
    home: loadHome, portfolio: loadPortfolio, scan: () => {},
    programs: loadPrograms, profile: loadProfile, legal: loadLegal,
  };
  if (loaders[name]) loaders[name]();
}

// ─── HOME ────────────────────────────────────────────────

async function loadHome() {
  updateDate();
  try {
    const res = await fetch(`${API}/api/home`);
    const data = await res.json();

    // Indices
    if (data.market?.indices?.length) {
      document.getElementById('market-card').innerHTML = data.market.indices.map(idx => `
        <div class="index-row">
          <div>
            <div class="index__name">${idx.nom}</div>
          </div>
          <div class="index__price">${formatNum(idx.price)}</div>
          <div class="index__change ${idx.change_pct >= 0 ? 'index__change--up' : 'index__change--down'}">
            ${idx.change_pct >= 0 ? '+' : ''}${idx.change_pct.toFixed(2)}%
          </div>
        </div>
      `).join('');
    } else {
      document.getElementById('market-card').innerHTML =
        '<div style="color:var(--text2);padding:12px;">Marchés indisponibles</div>';
    }

    // Commentary
    if (data.market?.commentary?.length) {
      document.getElementById('commentary-card').classList.remove('hidden');
      document.getElementById('commentary').innerHTML =
        data.market.commentary.map(c => `<div style="margin-bottom:6px;">${c}</div>`).join('');
    }

    // Portfolio mini
    const pf = data.portfolio_summary;
    if (pf && pf.positions?.length) {
      document.getElementById('home-portfolio').innerHTML = `
        <div class="card">
          <div class="card__title">Portefeuille</div>
          <div class="portfolio-hero">
            <div class="portfolio-hero__value">${pf.total_value_eur.toFixed(2)} EUR</div>
            <div class="portfolio-hero__pnl${pf.total_pnl_eur >= 0 ? 'portfolio-hero__pnl--positive' : 'portfolio-hero__pnl--negative'}">
              ${pf.total_pnl_eur >= 0 ? '+' : ''}${pf.total_pnl_eur.toFixed(2)} EUR
              (${pf.total_pnl_pct >= 0 ? '+' : ''}${pf.total_pnl_pct.toFixed(1)}%)
            </div>
          </div>
        </div>`;
    }

    // Programs mini
    if (data.programs?.length) {
      document.getElementById('home-programs').innerHTML = `
        <div class="card">
          <div class="card__title">Programmes actifs</div>
          ${data.programs.map(p => `
            <div class="position-row">
              <div>
                <div class="position-symbol">${p.nom}</div>
                <div class="position-detail">${p.risque} | ${p.horizon}</div>
              </div>
              <div style="text-align:right;font-weight:600;">${p.budget_initial.toFixed(0)} EUR</div>
            </div>
          `).join('')}
        </div>`;
    }
    // Portfolio opinion
    const op = data.portfolio_opinion;
    if (op && op.messages?.length) {
      const statusClass = op.status === 'positive' ? 'opinion-card--positive'
        : op.status === 'warning' ? 'opinion-card--warning'
        : op.status === 'setup' ? 'opinion-card--setup' : '';
      document.getElementById('home-portfolio').insertAdjacentHTML('afterbegin', `
        <div class="card opinion-card ${statusClass}">
          <div class="card__title">Avis sur votre portefeuille</div>
          ${op.messages.map(m => `<div class="opinion__msg">${m}</div>`).join('')}
          ${op.actions?.length ? op.actions.map(a =>
            `<button class="btn btn--outline btn--sm" onclick="showPage('${a.target}')" style="margin-top:8px;">${a.label}</button>`
          ).join('') : ''}
          ${op.disclaimer ? `<div class="opinion__disclaimer">${op.disclaimer}</div>` : ''}
        </div>`);
    }
  } catch (e) {
    document.getElementById('market-card').innerHTML =
      '<div class="alert alert--error" style="margin:0;">Erreur de connexion au serveur</div>';
  }
}

// ─── PORTFOLIO ───────────────────────────────────────────

async function loadPortfolio() {
  const el = document.getElementById('portfolio-content');
  el.innerHTML = '<div class="loading"><div class="spinner"></div>Chargement...</div>';

  try {
    const res = await fetch(`${API}/api/portfolio`);
    const pf = await res.json();

    let html = `
      <div class="card">
        <div class="portfolio-hero">
          <div class="portfolio-hero__value">${pf.total_value_eur.toFixed(2)} EUR</div>
          <div class="portfolio-hero__pnl${pf.total_pnl_eur >= 0 ? 'portfolio-hero__pnl--positive' : 'portfolio-hero__pnl--negative'}">
            ${pf.total_pnl_eur >= 0 ? '+' : ''}${pf.total_pnl_eur.toFixed(2)} EUR
            (${pf.total_pnl_pct >= 0 ? '+' : ''}${pf.total_pnl_pct.toFixed(1)}%)
          </div>
          <div style="color:var(--text2);margin-top:8px;">Cash: ${pf.cash_eur.toFixed(2)} EUR</div>
        </div>
      </div>`;

    if (pf.positions?.length) {
      html += '<div class="card"><div class="card__title">Positions</div>';
      pf.positions.forEach(p => {
        const pnlClass = p.pnl_eur >= 0 ? 'positive' : 'negative';
        html += `
          <div class="position-row">
            <div>
              <div class="position-symbol">${p.symbol}</div>
              <div class="position-detail">${p.invested.toFixed(2)} EUR investi | ${p.weight_pct.toFixed(1)}%</div>
            </div>
            <div class="position-pnl">
              <div class="portfolio-hero__pnl ${pnlClass}" style="font-size:15px;">
                ${p.pnl_eur >= 0 ? '+' : ''}${p.pnl_eur.toFixed(2)} EUR
              </div>
              <div style="font-size:12px;color:var(--text2);">
                ${p.pnl_pct >= 0 ? '+' : ''}${p.pnl_pct.toFixed(1)}%
              </div>
            </div>
          </div>`;
      });
      html += '</div>';
    } else {
      html += '<div class="card"><div style="color:var(--text2);text-align:center;padding:20px;">Aucune position</div></div>';
    }

    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = '<div class="card"><div style="color:var(--red);">Erreur de chargement</div></div>';
  }
}

// ─── SCAN ────────────────────────────────────────────────

async function runScan() {
  const el = document.getElementById('scan-results');
  el.innerHTML = '<div class="loading"><div class="spinner"></div>Scan en cours... (30-60s)</div>';

  try {
    const res = await fetch(`${API}/api/scan`);
    const data = await res.json();

    let html = `
      <div class="card" style="margin-top:12px;">
        <div class="card__title">
          ${data.summary.buy} BUY | ${data.summary.sell} SELL | ${data.summary.hold} HOLD
        </div>`;

    data.results.forEach(r => {
      html += `
        <div class="scan-row">
          <div>
            <div style="font-weight:600;">${r.symbol}</div>
            <div style="font-size:11px;color:var(--text2);">
              Score: ${r.score} | RSI: ${r.rsi ? r.rsi.toFixed(0) : 'N/A'}
            </div>
          </div>
          <div style="text-align:right;">
            <span class="badge badge--${r.signal.toLowerCase()}">${r.signal}</span>
            <div style="font-size:12px;color:var(--text2);margin-top:4px;">
              ${r.price ? formatNum(r.price) : ''}
            </div>
          </div>
        </div>`;
    });

    html += '</div>';

    // Bannières de risque si crypto ou levier dans les BUY
    const hasCrypto = data.results.some(r => r.signal === 'BUY' && ['BTC','ETH','SOL','XRP','DOGE','ADA','AVAX','MATIC'].includes(r.symbol));
    if (hasCrypto) {
      html += '<div class="risk-banner">Crypto-actifs : produits hautement spéculatifs présentant un risque de perte totale. Ne conviennent pas à tous les profils.</div>';
    }

    html += '<div class="risk-banner risk-banner--orange">Les signaux sont générés par un algorithme et ne constituent pas un conseil en investissement personnalisé.</div>';

    el.innerHTML = html;
    document.getElementById('btn-scan').textContent = 'Relancer le scan';
  } catch (e) {
    el.innerHTML = '<div class="alert alert--error">Erreur de scan. Réessayez.</div>';
    document.getElementById('btn-scan').textContent = 'Lancer le scan';
  }
}

// ─── PROGRAMS ────────────────────────────────────────────

async function loadPrograms() {
  const el = document.getElementById('programs-list');
  el.innerHTML = '<div class="loading"><div class="spinner"></div>Chargement...</div>';

  try {
    const res = await fetch(`${API}/api/programs`);
    const data = await res.json();

    if (!data.programs.length) {
      el.innerHTML = '<div style="color:var(--text2);text-align:center;padding:30px;">Aucun programme</div>';
      return;
    }

    el.innerHTML = data.programs.map(p => `
      <div class="program-card" onclick="showProgramDetail('${p.id}')">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <div>
            <div style="font-weight:700;font-size:16px;">${p.nom}</div>
            <div style="font-size:12px;color:var(--text2);margin-top:4px;">
              ${p.risque} | ${p.horizon} | ${p.duree_mois || '?'} mois
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-size:20px;font-weight:700;">${p.budget_initial.toFixed(0)} EUR</div>
            <div style="font-size:11px;color:var(--text2);">${p.enveloppe_preferee || 'CTO'}</div>
          </div>
        </div>
        ${p.allocation ? `
          <div style="margin-top:12px;border-top:1px solid var(--border);padding-top:10px;">
            ${p.allocation.slice(0, 4).map(a => `
              <div style="display:flex;justify-content:space-between;font-size:12px;padding:3px 0;">
                <span>${a.instrument?.nom || a.categorie}</span>
                <span style="color:var(--accent);">${a.pct}% (${a.montant_eur.toFixed(1)} EUR)</span>
              </div>
            `).join('')}
            ${p.allocation.length > 4 ? `<div style="font-size:11px;color:var(--text2);">+${p.allocation.length - 4} autres...</div>` : ''}
          </div>
        ` : ''}
      </div>
    `).join('');
  } catch (e) {
    el.innerHTML = '<div style="color:var(--red);padding:20px;">Erreur</div>';
  }
}

async function showProgramDetail(id) {
  try {
    const res = await fetch(`${API}/api/programs/${id}`);
    const p = await res.json();

    const el = document.getElementById('programs-list');
    let html = `
      <div class="card">
        <button class="btn btn--outline" onclick="loadPrograms()" style="margin:0 0 16px;width:auto;padding:8px 16px;">
          Retour
        </button>
        <h2 style="font-size:20px;">${p.nom}</h2>
        <div style="margin:12px 0;color:var(--text2);">
          Budget: ${p.budget_initial.toFixed(2)} EUR | ${p.risque} | ${p.horizon} (${p.duree_mois} mois)
          <br>Banques: ${(p.banques || []).join(', ')} | Enveloppe: ${p.enveloppe_preferee}
          ${p.dca_enabled ? `<br>DCA: ${p.dca_montant} EUR / ${p.dca_frequence}` : ''}
        </div>
      </div>`;

    if (p.allocation?.length) {
      p.allocation.forEach(a => {
        const j = a.justification || {};
        html += `
          <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
              <div style="font-weight:700;">${a.instrument?.nom || a.categorie}</div>
              <span class="badge badge--buy">${a.pct}% = ${a.montant_eur.toFixed(2)} EUR</span>
            </div>
            <div style="font-size:12px;color:var(--text2);margin-bottom:8px;">
              ${a.instrument?.symbol || ''} | ${(a.banques_disponibles || []).join(', ')}
            </div>
            ${j.pourquoi_cet_actif ? `
              <div class="justify">
                <div class="justify__label">Pourquoi cet actif</div>
                ${j.pourquoi_cet_actif}
              </div>` : ''}
            ${j.pourquoi_cette_enveloppe ? `
              <div class="justify">
                <div class="justify__label">Enveloppe</div>
                ${j.pourquoi_cette_enveloppe}
              </div>` : ''}
            ${j.pourquoi_cette_banque ? `
              <div class="justify">
                <div class="justify__label">Banque</div>
                ${j.pourquoi_cette_banque}
              </div>` : ''}
            ${j.impact_fiscal ? `
              <div class="justify">
                <div class="justify__label">Impact fiscal</div>
                Gain estim\u00e9: ${j.impact_fiscal.gain_brut_estime?.toFixed(2) || '?'} EUR |
                Imp\u00f4t: ${j.impact_fiscal.impot_estime?.toFixed(2) || '?'} EUR |
                Net: ${j.impact_fiscal.gain_net_estime?.toFixed(2) || '?'} EUR
                <br>${j.impact_fiscal.conseil || ''}
              </div>` : ''}
            ${j.risques?.length ? `
              <div class="justify justify--risk">
                <div class="justify__label">Risques</div>
                ${j.risques.map(r => `- ${r}`).join('<br>')}
              </div>` : ''}
            ${j.alternatives?.length ? `
              <div class="justify">
                <div class="justify__label">Alternatives</div>
                ${j.alternatives.map(a => `- ${a}`).join('<br>')}
              </div>` : ''}
          </div>`;
      });
    }

    html += `
      <div style="padding:16px;">
        <button class="btn btn--danger" onclick="deleteProgram('${p.id}')">Supprimer ce programme</button>
      </div>`;

    el.innerHTML = html;
    document.getElementById('program-form').classList.add('hidden');
  } catch (e) {
    console.error(e);
  }
}

function showCreateProgram() {
  const el = document.getElementById('program-form');
  el.classList.remove('hidden');
  el.innerHTML = `
    <div class="card">
      <div class="card__title">Nouveau programme</div>
      <div class="form-group">
        <label class="form-label">Nom</label>
        <input class="form-input" id="pg-nom" value="Mon programme" />
      </div>
      <div class="form-group">
        <label class="form-label">Budget (EUR)</label>
        <input class="form-input" id="pg-budget" type="number" value="100" />
      </div>
      <div class="form-group">
        <label class="form-label">Horizon</label>
        <select class="form-select" id="pg-horizon">
          <option value="court">Court terme (&lt;1 an)</option>
          <option value="moyen">Moyen terme (1-5 ans)</option>
          <option value="long">Long terme (&gt;5 ans)</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Dur\u00e9e (mois)</label>
        <input class="form-input" id="pg-duree" type="number" value="6" />
      </div>
      <div class="form-group">
        <label class="form-label">Risque</label>
        <select class="form-select" id="pg-risque">
          <option value="prudent">Prudent (2-4%)</option>
          <option value="equilibre" selected>Equilibr\u00e9 (4-7%)</option>
          <option value="dynamique">Dynamique (7-12%)</option>
          <option value="agressif">Agressif (&gt;12%)</option>
        </select>
      </div>
      <div class="form-group">
        <label class="form-label">Banque(s)</label>
        <input class="form-input" id="pg-banques" value="Revolut" />
      </div>
      <div class="form-group">
        <label class="form-label">Enveloppe</label>
        <select class="form-select" id="pg-enveloppe">
          <option value="cto">CTO</option>
          <option value="pea">PEA</option>
          <option value="assurance_vie">Assurance-vie</option>
          <option value="per">PER</option>
        </select>
      </div>
      <button class="btn btn--success" onclick="createProgram()">Cr\u00e9er le programme</button>
      <button class="btn btn--outline" onclick="document.getElementById('program-form').classList.add('hidden')">Annuler</button>
    </div>`;
}

async function createProgram() {
  const body = {
    nom: document.getElementById('pg-nom').value,
    budget_initial: parseFloat(document.getElementById('pg-budget').value),
    horizon: document.getElementById('pg-horizon').value,
    duree_mois: parseInt(document.getElementById('pg-duree').value),
    risque: document.getElementById('pg-risque').value,
    banques: document.getElementById('pg-banques').value.split(',').map(s => s.trim()),
    enveloppe_preferee: document.getElementById('pg-enveloppe').value,
  };

  try {
    const res = await fetch(`${API}/api/programs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      document.getElementById('program-form').classList.add('hidden');
      showToast('Programme cr\u00e9\u00e9 !', 'success');
      showProgramDetail(data.program.id);
    } else {
      showToast(data.detail || 'Erreur de cr\u00e9ation', 'error');
    }
  } catch (e) {
    showToast('Erreur de connexion', 'error');
  }
}

async function deleteProgram(id) {
  if (!confirm('Supprimer ce programme ? Cette action est irr\u00e9versible.')) return;
  try {
    await fetch(`${API}/api/programs/${id}`, { method: 'DELETE' });
    showToast('Programme supprim\u00e9', 'success');
    loadPrograms();
  } catch (e) {
    showToast('Erreur de suppression', 'error');
  }
}

// ─── PROFILE ─────────────────────────────────────────────

async function loadProfile() {
  const el = document.getElementById('profile-content');
  try {
    const res = await fetch(`${API}/api/profile`);
    const data = await res.json();

    if (data.exists) {
      const p = data.profile;
      el.innerHTML = `
        <div class="card">
          <div class="card__title">Votre profil</div>
          <div style="line-height:2;">
            <b>${p.prenom}</b> | ${p.age} ans<br>
            TMI: ${(p.tmi * 100).toFixed(0)}% | Fiscalit\u00e9: ${p.option_fiscale?.toUpperCase()}<br>
            Taux gains: ${(p.taux_imposition_gains * 100).toFixed(1)}%<br>
            Risque: ${p.profil_risque} | Horizon: ${p.horizon_global}<br>
            Banques: ${(p.banques || []).join(', ')}<br>
            ${p.has_pea ? `PEA: ${p.pea_age_ans} ans` : 'Pas de PEA'}
            ${p.has_assurance_vie ? ` | AV: ${p.av_age_ans} ans` : ''}
            ${p.has_per ? ' | PER' : ''}
          </div>
        </div>
        <div style="padding:0 16px;">
          <button class="btn btn--outline" onclick="showProfileForm()">Modifier le profil</button>
          <button class="btn btn--primary" onclick="testNotification()">Tester les notifications</button>
        </div>`;
    } else {
      showProfileForm();
    }
  } catch (e) {
    el.innerHTML = '<div style="color:var(--red);padding:20px;">Erreur</div>';
  }
}

function showProfileForm() {
  const el = document.getElementById('profile-content');
  el.innerHTML = `
    <div class="card">
      <div class="card__title">Configuration du profil</div>
      <div class="form-group"><label class="form-label">Pr\u00e9nom</label>
        <input class="form-input" id="pf-prenom" value="Investisseur"/></div>
      <div class="form-group"><label class="form-label">Age</label>
        <input class="form-input" id="pf-age" type="number" value="30"/></div>
      <div class="form-group"><label class="form-label">Revenu annuel net (EUR)</label>
        <input class="form-input" id="pf-revenu" type="number" value="30000"/></div>
      <div class="form-group"><label class="form-label">Situation</label>
        <select class="form-select" id="pf-situation">
          <option value="celibataire">C\u00e9libataire</option>
          <option value="marie_pacse">Mari\u00e9/Pacs\u00e9</option>
        </select></div>
      <div class="form-group"><label class="form-label">Parts fiscales</label>
        <input class="form-input" id="pf-parts" type="number" step="0.5" value="1"/></div>
      <div class="form-group"><label class="form-label">Fiscalit\u00e9</label>
        <select class="form-select" id="pf-fiscal">
          <option value="pfu">PFU (Flat Tax 30%)</option>
          <option value="bareme">Bar\u00e8me progressif</option>
        </select></div>
      <div class="form-group"><label class="form-label">Profil de risque</label>
        <select class="form-select" id="pf-risque">
          <option value="prudent">Prudent</option>
          <option value="equilibre">Equilibr\u00e9</option>
          <option value="dynamique">Dynamique</option>
          <option value="agressif">Agressif</option>
        </select></div>
      <div class="form-group"><label class="form-label">Banques (s\u00e9par\u00e9es par ,)</label>
        <input class="form-input" id="pf-banques" value="Revolut"/></div>
      <div class="form-group"><label class="form-checkbox">
        <input type="checkbox" id="pf-pea"/> J'ai un PEA</label></div>
      <div class="form-group"><label class="form-checkbox">
        <input type="checkbox" id="pf-av"/> J'ai une assurance-vie</label></div>
      <div class="form-group"><label class="form-checkbox">
        <input type="checkbox" id="pf-per"/> J'ai un PER</label></div>
      <div class="divider"></div>
      <div class="form-group"><label class="form-checkbox">
        <input type="checkbox" id="pf-risque-ok"/> Je comprends que tout investissement comporte un risque de perte en capital</label></div>
      <div class="form-group"><label class="form-checkbox">
        <input type="checkbox" id="pf-complexe-ok"/> Je comprends les risques des produits complexes (crypto, ETF levier)</label></div>
      <div class="divider"></div>
      <div class="form-group" style="background:var(--bg3);padding:12px;border-radius:8px;">
        <div style="font-size:11px;color:var(--text2);margin-bottom:8px;line-height:1.5;">
          En cochant cette case, j'accepte que mes donn\u00e9es personnelles soient trait\u00e9es
          conform\u00e9ment \u00e0 la <a href="#" onclick="showPage('legal');return false;" style="color:var(--accent);">politique de confidentialit\u00e9</a>
          pour g\u00e9n\u00e9rer des recommandations personnalis\u00e9es.
        </div>
        <label class="form-checkbox">
          <input type="checkbox" id="pf-rgpd"/> J'accepte le traitement de mes donn\u00e9es (RGPD)</label>
      </div>
      <button class="btn btn--success" onclick="saveProfile()">Enregistrer</button>
    </div>`;
}

async function saveProfile() {
  const body = {
    prenom: document.getElementById('pf-prenom').value,
    age: parseInt(document.getElementById('pf-age').value),
    revenu_annuel_net: parseInt(document.getElementById('pf-revenu').value),
    situation_familiale: document.getElementById('pf-situation').value,
    nb_parts_fiscales: parseFloat(document.getElementById('pf-parts').value),
    option_fiscale: document.getElementById('pf-fiscal').value,
    profil_risque: document.getElementById('pf-risque').value,
    banques: document.getElementById('pf-banques').value.split(',').map(s => s.trim()),
    has_pea: document.getElementById('pf-pea').checked,
    has_assurance_vie: document.getElementById('pf-av').checked,
    has_per: document.getElementById('pf-per').checked,
    has_cto: true,
    comprend_risque_perte: document.getElementById('pf-risque-ok').checked,
    comprend_produits_complexes: document.getElementById('pf-complexe-ok').checked,
    rgpd_consent: document.getElementById('pf-rgpd').checked,
  };

  if (!body.rgpd_consent) {
    showToast('Le consentement RGPD est obligatoire.', 'error');
    return;
  }

  try {
    const res = await fetch(`${API}/api/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast('Profil enregistr\u00e9 !', 'success');
      loadProfile();
    } else {
      showToast(data.detail || 'Erreur de sauvegarde', 'error');
    }
  } catch (e) {
    showToast('Erreur de connexion', 'error');
  }
}

async function testNotification() {
  try {
    const res = await fetch(`${API}/api/push/test`, { method: 'POST' });
    const data = await res.json();
    showToast(`Notification envoy\u00e9e (${data.sent || 0} destinataire(s))`, 'success');
  } catch (e) {
    showToast('Erreur d\'envoi de notification', 'error');
  }
}

// ─── PUSH NOTIFICATIONS ─────────────────────────────────

async function initPush() {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) return;

  try {
    const reg = await navigator.serviceWorker.register('/sw.js');
    const permission = Notification.permission;

    if (permission === 'default') {
      document.getElementById('notif-prompt').classList.remove('hidden');
    } else if (permission === 'granted') {
      await subscribePush(reg);
    }
  } catch (e) {
    console.error('SW registration failed:', e);
  }
}

async function requestNotifPermission() {
  const permission = await Notification.requestPermission();
  document.getElementById('notif-prompt').classList.add('hidden');

  if (permission === 'granted') {
    const reg = await navigator.serviceWorker.ready;
    await subscribePush(reg);
  }
}

async function subscribePush(reg) {
  try {
    const keyRes = await fetch(`${API}/api/push/vapid-key`);
    const { publicKey } = await keyRes.json();

    if (!publicKey || publicKey === 'GENERATE_WITH_vapid_gen') return;

    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(publicKey),
    });

    await fetch(`${API}/api/push/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sub.toJSON()),
    });
  } catch (e) {
    console.error('Push subscription failed:', e);
  }
}

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const raw = atob(base64);
  const arr = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
  return arr;
}

// ─── UTILS ───────────────────────────────────────────────

function updateDate() {
  const now = new Date();
  const days = ['Dimanche', 'Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi'];
  const months = ['janvier', 'f\u00e9vrier', 'mars', 'avril', 'mai', 'juin',
    'juillet', 'ao\u00fbt', 'septembre', 'octobre', 'novembre', 'd\u00e9cembre'];
  document.getElementById('header-date').textContent =
    `${days[now.getDay()]} ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()} - ${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`;
}

function formatNum(n) {
  if (n >= 1000) return n.toLocaleString('fr-FR', { maximumFractionDigits: 2 });
  return n.toFixed(2);
}

// ─── TOAST NOTIFICATIONS ─────────────────────────────────

function showToast(message, type = 'info') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ─── LEGAL PAGE ──────────────────────────────────────────

async function loadLegal() {
  const el = document.getElementById('legal-content');
  el.innerHTML = '<div class="loading"><div class="spinner"></div><span>Chargement...</span></div>';
  try {
    const res = await fetch(`${API}/api/legal`);
    const data = await res.json();
    let html = '';

    html += `<div class="risk-banner" style="margin:12px 0;">${data.disclaimer_amf}</div>`;

    const ml = data.mentions_legales;
    html += '<div class="legal-section">';
    html += `<div class="legal-section__title">${ml.titre}</div>`;
    for (const [key, val] of Object.entries(ml)) {
      if (key === 'titre') continue;
      html += `<div style="margin-bottom:12px;"><strong>${val.label}</strong><div class="legal-section__text">${val.text}</div></div>`;
    }
    html += '</div>';

    html += '<div class="legal-section">';
    html += `<div class="legal-section__title">${data.cgu.titre}</div>`;
    for (const s of data.cgu.sections) {
      html += `<div style="margin-bottom:12px;"><strong>${s.titre}</strong><div class="legal-section__text">${s.contenu}</div></div>`;
    }
    html += '</div>';

    html += '<div class="legal-section">';
    html += `<div class="legal-section__title">${data.politique_confidentialite.titre}</div>`;
    for (const s of data.politique_confidentialite.sections) {
      html += `<div style="margin-bottom:12px;"><strong>${s.titre}</strong><div class="legal-section__text">${s.contenu}</div></div>`;
    }
    html += '</div>';

    html += `<div class="risk-banner">${data.risk_crypto}</div>`;
    html += `<div class="risk-banner risk-banner--orange">${data.risk_leverage}</div>`;
    html += `<div class="legal-section"><div class="legal-section__title">Avertissement fiscal</div><div class="legal-section__text">${data.disclaimer_fiscal}</div></div>`;

    el.innerHTML = html;
  } catch (e) {
    el.innerHTML = '<div class="alert alert--error">Impossible de charger les informations.</div>';
  }
}

// ─── INIT ────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  loadHome();
  initPush();
});
