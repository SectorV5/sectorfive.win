import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, Navigate, useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || ""; // fallback to same-origin
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
    setLoading(false);
  }, []);

  const login = (token) => {
    localStorage.setItem('token', token);
    setIsAuthenticated(true);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);

// API helper with auth
const apiCall = async (url, options = {}) => {
  const token = localStorage.getItem('token');
  const headers = { ...options.headers };
  if (token) headers.Authorization = `Bearer ${token}`;
  return axios({ url: `${API}${url}`, ...options, headers });
};

// Components
const RetroButton = ({ children, onClick, className = "", type = "button", disabled = false }) => (
  <button type={type} onClick={onClick} disabled={disabled} className={`retro-button ${className} ${disabled ? 'disabled' : ''}`}>
    {children}
  </button>
);

const RetroWindow = ({ title, children, className = "" }) => (
  <div className={`retro-window ${className}`}>
    <div className="window-header">
      <div className="window-title">{title}</div>
    </div>
    <div className="window-content">{children}</div>
  </div>
);

const Footer = () => {
  return (
    <footer className="retro-footer">
      <div className="footer-content">
        <div className="footer-left">
          <p>© 2025 Made by <strong>Sectorfive</strong></p>
          <p>Licensed under <a href="https://www.gnu.org/licenses/gpl-3.0.html" target="_blank" rel="noopener noreferrer">GNU GPL v3</a></p>
        </div>
        <div className="footer-right">
          <p>Retro Personal Website Template</p>
          <p>Built with ❤️ for the retro web</p>
        </div>
      </div>
    </footer>
  );
};

const Navigation = ({ pages }) => {
  const { isAuthenticated, logout } = useAuth();
  return (
    <nav className="retro-nav">
      <div className="nav-container">
        <Link to="/" className="nav-logo">🏠 Personal Website</Link>
        <div className="nav-links">
          <Link to="/">Home</Link>
          <Link to="/blog">Blog</Link>
          <Link to="/gallery">Gallery</Link>
          <Link to="/contact">Contact</Link>
          {pages && pages.filter(p => !p.is_homepage).map(page => (
            <Link key={page.id} to={`/page/${page.slug}`}>{page.title}</Link>
          ))}
          <Link to="/login" className="admin-link">🔧 Admin</Link>
          {isAuthenticated && (<button onClick={logout} className="nav-button">Logout</button>)}
        </div>
      </div>
    </nav>
  );
};

const Home = () => {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const fetchContent = async () => {
      try {
        const response = await apiCall('/page/home');
        setContent(response.data.content || '<h1>Welcome!</h1><p>Edit this content in Admin → Pages.</p>');
      } catch (error) { setContent('<h1>Welcome!</h1><p>Edit this content in Admin → Pages.</p>'); }
      finally { setLoading(false); }
    };
    fetchContent();
  }, []);
  if (loading) return (<div className="loading"><div className="retro-spinner"></div>Loading...</div>);
  return (
    <RetroWindow title="🏠 Welcome to Your Website" className="main-content">
      <div className="content" dangerouslySetInnerHTML={{ __html: content }} />
    </RetroWindow>
  );
};

const Blog = () => {
  const [blogData, setBlogData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedTags, setSelectedTags] = useState('');
  const [page, setPage] = useState(1);
  const [allTags, setAllTags] = useState([]);
  
  useEffect(() => {
    fetchPosts();
    fetchTags();
  }, [search, selectedTags, page]);
  
  const fetchPosts = async () => {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '6',
        published: 'true'
      });
      if (search) params.append('search', search);
      if (selectedTags) params.append('tags', selectedTags);
      
      const response = await axios.get(`${API}/blog?${params}`);
      setBlogData(response.data);
    } catch (error) {
      console.error('Error fetching posts:', error);
    } finally { 
      setLoading(false); 
    }
  };
  
  const fetchTags = async () => {
    try {
      const response = await axios.get(`${API}/blog/tags`);
      setAllTags(response.data);
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  };
  
  if (loading) return <div className="loading">Loading blog posts...</div>;
  
  return (
    <RetroWindow title="📝 Blog Posts" className="main-content">
      {/* Search and Filter Controls */}
      <div className="blog-controls">
          <div className="search-section">
            <input 
              type="text" 
              placeholder="Search posts..." 
              value={search} 
              onChange={(e)=>setSearch(e.target.value)} 
              className="retro-input" 
            />
            <input 
              type="text" 
              placeholder="Filter by tags (comma-separated)..." 
              value={selectedTags} 
              onChange={(e)=>setSelectedTags(e.target.value)} 
              className="retro-input" 
            />
          </div>
          
          {/* Tag Cloud */}
          {allTags.length > 0 && (
            <div className="tag-cloud">
              <h4>Popular Tags:</h4>
              <div className="tags">
                {allTags.slice(0, 10).map(tag => (
                  <span 
                    key={tag.name} 
                    className={`tag ${selectedTags.includes(tag.name) ? 'active' : ''}`}
                    onClick={() => {
                      if (selectedTags.includes(tag.name)) {
                        setSelectedTags(selectedTags.replace(tag.name, '').replace(/,\s*,/g, ',').replace(/^,|,$/g, ''));
                      } else {
                        setSelectedTags(selectedTags ? `${selectedTags}, ${tag.name}` : tag.name);
                      }
                    }}
                  >
                    {tag.name} ({tag.count})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {blogData && blogData.posts && blogData.posts.length > 0 ? (
          <>
            <div className="blog-posts">
              {blogData.posts.map(post => (
                <div key={post.id} className="blog-post-preview">
                  {post.featured_image && (
                    <div className="post-image">
                      <img src={post.featured_image} alt={post.title} />
                    </div>
                  )}
                  <div className="post-header">
                    <h3><Link to={`/blog/${post.slug}`}>{post.title}</Link></h3>
                    <div className="post-meta">
                      📅 {new Date(post.created_at).toLocaleDateString()}
                      {post.author && <span> • ✍️ {post.author}</span>}
                    </div>
                  </div>
                  
                  {post.tags && post.tags.length > 0 && (
                    <div className="post-tags">
                      {post.tags.map(tag => (
                        <span key={tag} className="tag" onClick={() => setSelectedTags(tag)}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  
                  <div className="post-content">
                    {post.excerpt || (post.content && post.content.length > 200 ? post.content.substring(0, 200) + '...' : post.content || '')}
                  </div>
                  
                  <Link to={`/blog/${post.slug}`} className="read-more">Read More →</Link>
                </div>
              ))}
            </div>
            
            {blogData && blogData.pagination && blogData.pagination.total_pages > 1 && (
              <div className="pagination">
                <button 
                  onClick={() => setPage(Math.max(1, page - 1))} 
                  disabled={page === 1}
                >
                  Previous
                </button>
                <span className="current-page">
                  Page {blogData.pagination.current_page} of {blogData.pagination.total_pages}
                </span>
                <button 
                  onClick={() => setPage(Math.min(blogData.pagination.total_pages, page + 1))} 
                  disabled={page === blogData.pagination.total_pages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        ) : (
          <p>No blog posts found. {search || selectedTags ? 'Try adjusting your search or filters.' : 'Check back soon!'}</p>
        )}
    </RetroWindow>
  );
};

const BlogPost = () => {
  const { slug } = useParams();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const fetchPost = async () => {
      try {
        const response = await axios.get(`${API}/blog/${slug}`);
        setPost(response.data);
      } catch (error) {} finally { setLoading(false); }
    };
    fetchPost();
  }, [slug]);
  if (loading) return <div className="loading">Loading post...</div>;
  if (!post) return <div className="error">Post not found 😕</div>;
  return (
    <RetroWindow title={post.title} className="main-content">
      <div className="post-meta">📅 {new Date(post.created_at).toLocaleDateString()}</div>
      <div className="content" dangerouslySetInnerHTML={{ __html: post.content }} />
    </RetroWindow>
  );
};

const Gallery = () => {
  const [galleryData, setGalleryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedTags, setSelectedTags] = useState('');
  const [featuredOnly, setFeaturedOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [allTags, setAllTags] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);
  
  useEffect(() => {
    fetchImages();
    fetchTags();
  }, [search, selectedTags, featuredOnly, page]);
  
  const fetchImages = async () => {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '12'
      });
      if (search) params.append('search', search);
      if (selectedTags) params.append('tags', selectedTags);
      if (featuredOnly) params.append('featured_only', 'true');
      
      const response = await axios.get(`${API}/gallery?${params}`);
      setGalleryData(response.data);
    } catch (error) {
      console.error('Error fetching gallery images:', error);
    } finally { 
      setLoading(false); 
    }
  };
  
  const fetchTags = async () => {
    try {
      const response = await axios.get(`${API}/gallery/tags`);
      setAllTags(response.data);
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  };
  
  if (loading) return <div className="loading">Loading gallery...</div>;
  
  return (
    <RetroWindow title="🖼️ Image Gallery" className="main-content">
      {/* Search and Filter Controls */}
        <div className="gallery-controls">
          <div className="search-section">
            <input 
              type="text" 
              placeholder="Search images..." 
              value={search} 
              onChange={(e) => setSearch(e.target.value)} 
              className="retro-input" 
            />
            <input 
              type="text" 
              placeholder="Filter by tags (comma-separated)..." 
              value={selectedTags} 
              onChange={(e) => setSelectedTags(e.target.value)} 
              className="retro-input" 
            />
            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={featuredOnly} 
                onChange={(e) => setFeaturedOnly(e.target.checked)} 
              />
              Featured images only
            </label>
          </div>
          
          {/* Tag Cloud */}
          {allTags.length > 0 && (
            <div className="tag-cloud">
              <h4>Popular Tags:</h4>
              <div className="tags">
                {allTags.slice(0, 10).map(tag => (
                  <span 
                    key={tag.name} 
                    className={`tag ${selectedTags.includes(tag.name) ? 'active' : ''}`}
                    onClick={() => {
                      if (selectedTags.includes(tag.name)) {
                        setSelectedTags(selectedTags.replace(tag.name, '').replace(/,\s*,/g, ',').replace(/^,|,$/g, ''));
                      } else {
                        setSelectedTags(selectedTags ? `${selectedTags}, ${tag.name}` : tag.name);
                      }
                    }}
                  >
                    {tag.name} ({tag.count})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {galleryData && galleryData.images.length > 0 ? (
          <>
            <div className="gallery-grid">
              {galleryData.images.map(image => (
                <div key={image.id} className="gallery-item" onClick={() => setSelectedImage(image)}>
                  <div className="image-container">
                    <img src={image.file_url} alt={image.title} loading="lazy" />
                    {image.is_featured && <div className="featured-badge">⭐ Featured</div>}
                  </div>
                  <div className="image-info">
                    <h4>{image.title}</h4>
                    {image.description && <p className="description">{image.description}</p>}
                    {image.tags && image.tags.length > 0 && (
                      <div className="image-tags">
                        {image.tags.map(tag => (
                          <span key={tag} className="tag" onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTags(tag);
                          }}>
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="image-meta">
                      📅 {new Date(image.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {galleryData.pagination && galleryData.pagination.total_pages > 1 && (
              <div className="pagination">
                <button 
                  onClick={() => setPage(Math.max(1, page - 1))} 
                  disabled={page === 1}
                >
                  Previous
                </button>
                <span className="current-page">
                  Page {galleryData.pagination.current_page} of {galleryData.pagination.total_pages}
                </span>
                <button 
                  onClick={() => setPage(Math.min(galleryData.pagination.total_pages, page + 1))} 
                  disabled={page === galleryData.pagination.total_pages}
                >
                  Next
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="empty-gallery">
            <p>No images found in the gallery. {search || selectedTags ? 'Try adjusting your search or filters.' : 'Check back soon!'}</p>
          </div>
        )}
        
        {/* Image Modal */}
        {selectedImage && (
          <div className="modal-overlay" onClick={() => setSelectedImage(null)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <button className="modal-close" onClick={() => setSelectedImage(null)}>×</button>
              <img src={selectedImage.file_url} alt={selectedImage.title} />
              <div className="modal-info">
                <h3>{selectedImage.title}</h3>
                {selectedImage.description && <p>{selectedImage.description}</p>}
                {selectedImage.tags && selectedImage.tags.length > 0 && (
                  <div className="modal-tags">
                    {selectedImage.tags.map(tag => (
                      <span key={tag} className="tag">{tag}</span>
                    ))}
                  </div>
                )}
                <div className="modal-meta">
                  📅 {new Date(selectedImage.created_at).toLocaleDateString()}
                  {selectedImage.uploaded_by && <span> • 👤 {selectedImage.uploaded_by}</span>}
                </div>
              </div>
            </div>
          </div>
        )}
      </RetroWindow>
  );
};

const Contact = () => {
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true); setError('');
    try {
      await axios.post(`${API}/contact`, formData);
      setSent(true); setFormData({ name: '', email: '', message: '' });
    } catch (error) {
      if (error.response?.status === 429) setError(error.response.data.detail);
      else setError('Error sending message. Please try again.');
    } finally { setSending(false); }
  };
  return (
    <RetroWindow title="📬 Contact Me" className="main-content">
      {sent ? (<div className="success-message">✅ Message sent successfully! I'll get back to you soon.</div>) : (
        <form onSubmit={handleSubmit} className="contact-form">
          {error && <div className="error-message">{error}</div>}
          <div className="form-group"><label>Name:</label><input type="text" name="name" value={formData.name} onChange={(e)=>setFormData({...formData, name:e.target.value})} required className="retro-input" /></div>
          <div className="form-group"><label>Email:</label><input type="email" name="email" value={formData.email} onChange={(e)=>setFormData({...formData, email:e.target.value})} required className="retro-input" /></div>
          <div className="form-group"><label>Message:</label><textarea name="message" value={formData.message} onChange={(e)=>setFormData({...formData, message:e.target.value})} required rows="5" className="retro-textarea" /></div>
          <RetroButton type="submit" disabled={sending}>{sending ? <>🔄 Sending...</> : <>📨 Send Message</>}</RetroButton>
        </form>
      )}
    </RetroWindow>
  );
};

const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const handleSubmit = async (e) => {
    e.preventDefault(); 
    setLoading(true); 
    setError('');
    
    try {
      const response = await axios.post(`${API}/login`, credentials);
      login(response.data.access_token);
      
      if (response.data.must_change_password) {
        navigate('/first-setup');
      } else {
        navigate('/management-panel');
      }
    } catch (error) { 
      setError('Invalid credentials. Please check your username and password.'); 
    } finally { 
      setLoading(false); 
    }
  };
  
  return (
    <RetroWindow title="🔐 Admin Login" className="login-window">
        <div className="login-form">
          {error && <div className="error-message">{error}</div>}
          
          <div className="login-info">
            <h3>Welcome to Admin Panel</h3>
            <p>Default credentials for first login:</p>
            <div className="default-creds">
              <strong>Username:</strong> admin<br/>
              <strong>Password:</strong> admin
            </div>
            <p><small>You'll be asked to change these on first login for security.</small></p>
          </div>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Username:</label>
              <input 
                type="text" 
                className="retro-input" 
                value={credentials.username}
                onChange={(e) => setCredentials({...credentials, username: e.target.value})}
                required 
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>Password:</label>
              <input 
                type="password" 
                className="retro-input" 
                value={credentials.password}
                onChange={(e) => setCredentials({...credentials, password: e.target.value})}
                required 
                disabled={loading}
              />
            </div>
            <button type="submit" className="retro-button" disabled={loading}>
              {loading ? '🔄 Logging in...' : '🔐 Login'}
            </button>
          </form>
        </div>
      </RetroWindow>
  );
};

const FirstSetup = () => {
  const { isAuthenticated } = useAuth();
  const [me, setMe] = useState(null);
  const [form, setForm] = useState({ old_password: '', new_username: '', new_password: '' });
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();
  useEffect(() => { apiCall('/me').then(r=>setMe(r.data)).catch(()=>{}); }, []);
  if (!isAuthenticated) return <Navigate to="/login" />;
  const submit = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const fd = new FormData();
      fd.append('old_password', form.old_password);
      fd.append('new_username', form.new_username);
      fd.append('new_password', form.new_password);
      await apiCall('/change-credentials', { method: 'POST', data: fd });
      alert('Credentials updated. Please login again.');
      localStorage.removeItem('token');
      navigate('/login');
    } catch (e) { alert(e.response?.data?.detail || 'Failed to update credentials'); } finally { setSaving(false); }
  };
  return (
    <RetroWindow title="🛡️ First-time Setup" className="login-window">
      <p>Please change the default admin credentials to continue.</p>
        {me && me.must_change_password === false && (
          <div className="success-message">Already updated. You can go to the <Link to="/management-panel">Admin Dashboard</Link>.</div>
        )}
        <form onSubmit={submit}>
          <div className="form-group"><label>Current Password:</label><input type="password" value={form.old_password} onChange={(e)=>setForm({...form, old_password:e.target.value})} required className="retro-input" /></div>
          <div className="form-group"><label>New Username:</label><input type="text" value={form.new_username} onChange={(e)=>setForm({...form, new_username:e.target.value})} required className="retro-input" /></div>
          <div className="form-group"><label>New Password:</label><input type="password" value={form.new_password} onChange={(e)=>setForm({...form, new_password:e.target.value})} required className="retro-input" /></div>
          <RetroButton type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save & Continue'}</RetroButton>
        </form>
      </RetroWindow>
  );
};

const Admin = () => {
  const { isAuthenticated } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [me, setMe] = useState(null);
  useEffect(() => { apiCall('/me').then(r=>setMe(r.data)).catch(()=>{}); }, []);
  if (!isAuthenticated) return <Navigate to="/login" />;
  if (me && me.must_change_password) return <Navigate to="/first-setup" />;
  return (
    <RetroWindow title="⚙️ Admin Dashboard" className="admin-window">
      <div className="admin-tabs">
          <button className={`tab-button ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>📊 Dashboard</button>
          <button className={`tab-button ${activeTab === 'pages' ? 'active' : ''}`} onClick={() => setActiveTab('pages')}>📄 Pages</button>
          <button className={`tab-button ${activeTab === 'blog' ? 'active' : ''}`} onClick={() => setActiveTab('blog')}>📝 Blog</button>
          <button className={`tab-button ${activeTab === 'gallery' ? 'active' : ''}`} onClick={() => setActiveTab('gallery')}>🖼️ Gallery</button>
          <button className={`tab-button ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => setActiveTab('analytics')}>📈 Analytics</button>
          <button className={`tab-button ${activeTab === 'contacts' ? 'active' : ''}`} onClick={() => setActiveTab('contacts')}>📧 Contacts</button>
          <button className={`tab-button ${activeTab === 'settings' ? 'active' : ''}`} onClick={() => setActiveTab('settings')}>⚙️ Settings</button>
        </div>
        <div className="tab-content">
          {activeTab === 'dashboard' && <AdminDashboard />}
          {activeTab === 'pages' && <AdminPages />}
          {activeTab === 'blog' && <AdminBlog />}
          {activeTab === 'gallery' && <AdminGallery />}
          {activeTab === 'analytics' && <AdminAnalytics />}
          {activeTab === 'contacts' && <AdminContacts />}
          {activeTab === 'settings' && <AdminSettings />}
        </div>
      </RetroWindow>
  );
};

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [analytics, contacts, pages, posts] = await Promise.all([
          apiCall('/analytics'), apiCall('/contact-messages'), apiCall('/pages'), axios.get(`${API}/blog`)
        ]);
        setStats({ totalVisits: analytics.data.total_visits, uniqueVisitors: analytics.data.unique_visitors, totalContacts: contacts.data.pagination.total_results, totalPages: pages.data.length, totalPosts: posts.data.length });
      } catch (error) {}
    };
    fetchStats();
  }, []);
  return (
    <div className="admin-dashboard">
      <h3>🎯 Quick Stats</h3>
      <div className="dashboard-stats">
        <div className="stat-card"><h4>📄 Pages</h4>{stats ? <p>Total: {stats.totalPages}</p> : <p>Loading...</p>}</div>
        <div className="stat-card"><h4>📝 Blog</h4>{stats ? <p>Total Posts: {stats.totalPosts}</p> : <p>Loading...</p>}</div>
        <div className="stat-card"><h4>📈 Analytics</h4>{stats ? (<><p>Total Visits: {stats.totalVisits}</p><p>Unique Visitors: {stats.uniqueVisitors}</p></>) : (<p>Loading stats...</p>)}</div>
        <div className="stat-card"><h4>📧 Contacts</h4>{stats ? (<p>Messages: {stats.totalContacts}</p>) : (<p>Loading...</p>)}</div>
      </div>
    </div>
  );
};

const quillModules = { toolbar: [[{ header: [1, 2, 3, false] }], ['bold', 'italic', 'underline', 'strike'], [{ list: 'ordered' }, { list: 'bullet' }], ['link', 'image'], ['clean']] };
const quillFormats = ['header','bold','italic','underline','strike','list','bullet','link','image'];

const AdminPages = () => {
  const [pages, setPages] = useState([]);
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  const [formData, setFormData] = useState({ title: '', slug: '', content: '' });
  useEffect(() => { fetchPages(); }, []);
  const fetchPages = async () => { try { const response = await apiCall('/pages'); setPages(response.data); } catch (error) {} };
  const handleCreate = async (e) => { e.preventDefault(); try { await apiCall('/pages', { method: 'POST', data: formData }); setCreating(false); setFormData({ title: '', slug: '', content: '' }); fetchPages(); } catch (error) { alert('Error creating page: ' + (error.response?.data?.detail || error.message)); } };
  const handleUpdate = async (e) => { e.preventDefault(); try { await apiCall(`/pages/${editing.id}`, { method: 'PUT', data: { title: formData.title, content: formData.content } }); setEditing(null); setFormData({ title: '', slug: '', content: '' }); fetchPages(); } catch (error) { alert('Error updating page: ' + (error.response?.data?.detail || error.message)); } };
  const handleDelete = async (page) => { if (page.is_homepage) { alert('Cannot delete homepage'); return; } if (window.confirm(`Delete page "${page.title}"?`)) { try { await apiCall(`/pages/${page.id}`, { method: 'DELETE' }); fetchPages(); } catch (error) { alert('Error deleting page: ' + (error.response?.data?.detail || error.message)); } } };
  const startEdit = (page) => { setEditing(page); setFormData({ title: page.title, slug: page.slug, content: page.content }); };
  const cancelEdit = () => { setEditing(null); setCreating(false); setFormData({ title: '', slug: '', content: '' }); };
  if (creating || editing) return (
    <div className="admin-section">
      <h3>{creating ? 'Create New Page' : `Edit: ${editing.title}`}</h3>
      <form onSubmit={creating ? handleCreate : handleUpdate}>
        <div className="form-group"><label>Title:</label><input type="text" value={formData.title} onChange={(e)=>setFormData({ ...formData, title: e.target.value })} required className="retro-input" /></div>
        {creating && (<div className="form-group"><label>Slug (URL path):</label><input type="text" value={formData.slug} onChange={(e)=>setFormData({ ...formData, slug: e.target.value })} required className="retro-input" placeholder="e.g., about-me" /></div>)}
        <div className="form-group"><label>Content:</label><div className="editor-container"><ReactQuill theme="snow" value={formData.content} onChange={(content)=>setFormData({ ...formData, content })} modules={quillModules} formats={quillFormats} /></div></div>
        <div className="admin-controls"><RetroButton type="submit">{creating ? 'Create Page' : 'Update Page'}</RetroButton><RetroButton type="button" onClick={cancelEdit}>Cancel</RetroButton></div>
      </form>
    </div>
  );
  return (
    <div className="admin-section">
      <div className="admin-controls"><h3>📄 Page Management</h3><RetroButton onClick={() => setCreating(true)}>Create New Page</RetroButton></div>
      <table className="admin-table"><thead><tr><th>Title</th><th>Slug</th><th>Created</th><th>Actions</th></tr></thead><tbody>{pages.map(page => (<tr key={page.id}><td>{page.title} {page.is_homepage && '(Homepage)'}</td><td>{page.slug}</td><td>{new Date(page.created_at).toLocaleDateString()}</td><td><RetroButton onClick={() => startEdit(page)}>Edit</RetroButton>{!page.is_homepage && (<RetroButton onClick={() => handleDelete(page)}>Delete</RetroButton>)}</td></tr>))}</tbody></table>
    </div>
  );
};

const AdminBlog = () => {
  const [blogData, setBlogData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  const [search, setSearch] = useState('');
  const [filterTags, setFilterTags] = useState('');
  const [filterAuthor, setFilterAuthor] = useState('');
  const [showDrafts, setShowDrafts] = useState(false);
  const [page, setPage] = useState(1);
  const [formData, setFormData] = useState({
    title: '', slug: '', content: '', excerpt: '', tags: [], 
    featured_image: '', published: true, meta_description: ''
  });
  const [tagInput, setTagInput] = useState('');
  
  useEffect(() => { fetchPosts(); }, [search, filterTags, filterAuthor, showDrafts, page]);
  
  const fetchPosts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '10'
      });
      if (search) params.append('search', search);
      if (filterTags) params.append('tags', filterTags);
      if (filterAuthor) params.append('author', filterAuthor);
      if (showDrafts !== null) params.append('published', (!showDrafts).toString());
      
      const response = await axios.get(`${API}/blog?${params}`);
      setBlogData(response.data);
    } catch (error) {
      console.error('Error fetching posts:', error);
    }
  };
  
  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const postData = {
        ...formData,
        tags: tagInput.split(',').map(tag => tag.trim()).filter(tag => tag)
      };
      await apiCall('/blog', { method: 'POST', data: postData });
      setCreating(false);
      resetForm();
      fetchPosts();
    } catch (error) {
      alert('Error creating post: ' + (error.response?.data?.detail || error.message));
    }
  };
  
  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const postData = {
        title: formData.title,
        content: formData.content,
        excerpt: formData.excerpt,
        tags: tagInput.split(',').map(tag => tag.trim()).filter(tag => tag),
        featured_image: formData.featured_image,
        published: formData.published,
        meta_description: formData.meta_description
      };
      await apiCall(`/blog/${editing.id}`, { method: 'PUT', data: postData });
      setEditing(null);
      resetForm();
      fetchPosts();
    } catch (error) {
      alert('Error updating post: ' + (error.response?.data?.detail || error.message));
    }
  };
  
  const handleDelete = async (post) => {
    if (window.confirm(`Delete post "${post.title}"?`)) {
      try {
        await apiCall(`/blog/${post.id}`, { method: 'DELETE' });
        fetchPosts();
      } catch (error) {
        alert('Error deleting post: ' + (error.response?.data?.detail || error.message));
      }
    }
  };
  
  const startEdit = (post) => {
    setEditing(post);
    setFormData({
      title: post.title,
      slug: post.slug,
      content: post.content,
      excerpt: post.excerpt || '',
      featured_image: post.featured_image || '',
      published: post.published,
      meta_description: post.meta_description || ''
    });
    setTagInput(post.tags ? post.tags.join(', ') : '');
  };
  
  const resetForm = () => {
    setFormData({
      title: '', slug: '', content: '', excerpt: '', tags: [],
      featured_image: '', published: true, meta_description: ''
    });
    setTagInput('');
  };
  
  const cancelEdit = () => {
    setEditing(null);
    setCreating(false);
    resetForm();
  };
  if (creating || editing) return (
    <div className="admin-section">
      <h3>{creating ? 'Create New Blog Post' : `Edit: ${editing.title}`}</h3>
      <form onSubmit={creating ? handleCreate : handleUpdate}>
        <div className="form-group">
          <label>Title:</label>
          <input 
            type="text" 
            value={formData.title} 
            onChange={(e)=>setFormData({ ...formData, title: e.target.value })} 
            required 
            className="retro-input" 
          />
        </div>
        
        {creating && (
          <div className="form-group">
            <label>Slug (URL path):</label>
            <input 
              type="text" 
              value={formData.slug} 
              onChange={(e)=>setFormData({ ...formData, slug: e.target.value })} 
              required 
              className="retro-input" 
              placeholder="e.g., my-first-post" 
            />
          </div>
        )}
        
        <div className="form-group">
          <label>Excerpt (optional):</label>
          <textarea 
            value={formData.excerpt} 
            onChange={(e)=>setFormData({ ...formData, excerpt: e.target.value })} 
            className="retro-textarea" 
            rows="3"
            placeholder="Brief description (auto-generated if empty)"
          />
        </div>
        
        <div className="form-group">
          <label>Tags (comma-separated):</label>
          <input 
            type="text" 
            value={tagInput} 
            onChange={(e)=>setTagInput(e.target.value)} 
            className="retro-input" 
            placeholder="e.g., tech, programming, tutorial"
          />
        </div>
        
        <div className="form-group">
          <label>Featured Image URL (optional):</label>
          <input 
            type="url" 
            value={formData.featured_image} 
            onChange={(e)=>setFormData({ ...formData, featured_image: e.target.value })} 
            className="retro-input" 
            placeholder="https://..."
          />
        </div>
        
        <div className="form-group">
          <label>Meta Description (SEO):</label>
          <textarea 
            value={formData.meta_description} 
            onChange={(e)=>setFormData({ ...formData, meta_description: e.target.value })} 
            className="retro-textarea" 
            rows="2"
            placeholder="SEO description for search engines"
          />
        </div>
        
        <div className="form-group">
          <label>
            <input 
              type="checkbox" 
              checked={formData.published} 
              onChange={(e)=>setFormData({ ...formData, published: e.target.checked })} 
            />
            {' '}Published (uncheck to save as draft)
          </label>
        </div>
        
        <div className="form-group">
          <label>Content:</label>
          <div className="editor-container">
            <ReactQuill 
              theme="snow" 
              value={formData.content} 
              onChange={(content)=>setFormData({ ...formData, content })} 
              modules={quillModules} 
              formats={quillFormats} 
            />
          </div>
        </div>
        
        <div className="admin-controls">
          <RetroButton type="submit">
            {creating ? 'Create Post' : 'Update Post'}
          </RetroButton>
          <RetroButton type="button" onClick={cancelEdit}>Cancel</RetroButton>
        </div>
      </form>
    </div>
  );
  return (
    <div className="admin-section">
      <div className="admin-controls">
        <h3>📝 Blog Management</h3>
        <RetroButton onClick={() => setCreating(true)}>Create New Post</RetroButton>
      </div>
      
      <div className="admin-controls">
        <input 
          type="text" 
          placeholder="Search posts..." 
          value={search} 
          onChange={(e)=>setSearch(e.target.value)} 
          className="retro-input" 
        />
        <input 
          type="text" 
          placeholder="Filter by tags..." 
          value={filterTags} 
          onChange={(e)=>setFilterTags(e.target.value)} 
          className="retro-input" 
        />
        <input 
          type="text" 
          placeholder="Filter by author..." 
          value={filterAuthor} 
          onChange={(e)=>setFilterAuthor(e.target.value)} 
          className="retro-input" 
        />
        <label>
          <input 
            type="checkbox" 
            checked={showDrafts} 
            onChange={(e)=>setShowDrafts(e.target.checked)} 
          />
          {' '}Show drafts only
        </label>
      </div>
      
      {blogData && (
        <>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Tags</th>
                <th>Author</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {blogData && blogData.posts ? blogData.posts.map(post => (
                <tr key={post.id}>
                  <td>{post.title}</td>
                  <td>
                    <span className={`status ${post.published ? 'published' : 'draft'}`}>
                      {post.published ? '✅ Published' : '📝 Draft'}
                    </span>
                  </td>
                  <td>{post.tags ? post.tags.join(', ') : ''}</td>
                  <td>{post.author}</td>
                  <td>{new Date(post.created_at).toLocaleDateString()}</td>
                  <td>
                    <RetroButton onClick={() => startEdit(post)}>Edit</RetroButton>
                    <RetroButton onClick={() => handleDelete(post)}>Delete</RetroButton>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan="6" style={{textAlign: 'center', padding: '20px'}}>
                    {loading ? 'Loading posts...' : 'No blog posts found'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          
          {blogData && blogData.pagination && blogData.pagination.total_pages > 1 && (
            <div className="pagination">
              <button 
                onClick={() => setPage(Math.max(1, page - 1))} 
                disabled={page === 1}
              >
                Previous
              </button>
              <span className="current-page">
                Page {blogData.pagination.current_page} of {blogData.pagination.total_pages}
              </span>
              <button 
                onClick={() => setPage(Math.min(blogData.pagination.total_pages, page + 1))} 
                disabled={page === blogData.pagination.total_pages}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

const AdminGallery = () => {
  const [galleryData, setGalleryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [editing, setEditing] = useState(null);
  const [search, setSearch] = useState('');
  const [selectedTags, setSelectedTags] = useState('');
  const [page, setPage] = useState(1);
  const [allTags, setAllTags] = useState([]);
  const [uploadForm, setUploadForm] = useState({
    title: '',
    description: '',
    tags: '',
    is_featured: false
  });

  useEffect(() => {
    fetchImages();
    fetchTags();
  }, [search, selectedTags, page]);

  const fetchImages = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '12'
      });
      if (search) params.append('search', search);
      if (selectedTags) params.append('tags', selectedTags);
      
      const response = await apiCall(`/gallery?${params}`);
      setGalleryData(response.data);
    } catch (error) {
      console.error('Error fetching gallery images:', error);
    } finally { 
      setLoading(false); 
    }
  };

  const fetchTags = async () => {
    try {
      const response = await apiCall('/gallery/tags');
      setAllTags(response.data || []);
    } catch (error) {
      console.error('Error fetching tags:', error);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!e.target.file.files[0]) return;
    
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', e.target.file.files[0]);
      formData.append('title', uploadForm.title);
      formData.append('description', uploadForm.description || '');
      formData.append('tags', uploadForm.tags);
      formData.append('is_featured', uploadForm.is_featured);
      
      await apiCall('/gallery', {
        method: 'POST',
        data: formData,
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setUploadForm({ title: '', description: '', tags: '', is_featured: false });
      e.target.reset();
      fetchImages();
      fetchTags();
      alert('Image uploaded successfully!');
    } catch (error) {
      alert('Error uploading image: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (imageId) => {
    if (!window.confirm('Delete this image? This action cannot be undone.')) return;
    
    try {
      await apiCall(`/gallery/${imageId}`, { method: 'DELETE' });
      fetchImages();
      fetchTags();
      alert('Image deleted successfully!');
    } catch (error) {
      alert('Error deleting image: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!editing) return;
    
    try {
      const updateData = {
        title: editing.title,
        description: editing.description,
        tags: editing.tags || [],
        is_featured: editing.is_featured
      };
      
      await apiCall(`/gallery/${editing.id}`, {
        method: 'PUT',
        data: updateData
      });
      
      setEditing(null);
      fetchImages();
      fetchTags();
      alert('Image updated successfully!');
    } catch (error) {
      alert('Error updating image: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading && !galleryData) return <div>Loading gallery...</div>;

  return (
    <div className="admin-section">
      <h3>🖼️ Gallery Management</h3>
      
      {/* Upload Form */}
      <div className="admin-subsection">
        <h4>Upload New Image</h4>
        <form onSubmit={handleUpload} className="upload-form">
          <div className="form-group">
            <label>Select Image:</label>
            <input type="file" name="file" accept="image/*" required className="retro-input" />
          </div>
          <div className="form-group">
            <label>Title:</label>
            <input 
              type="text" 
              value={uploadForm.title} 
              onChange={(e) => setUploadForm({...uploadForm, title: e.target.value})} 
              required 
              className="retro-input" 
            />
          </div>
          <div className="form-group">
            <label>Description:</label>
            <textarea 
              value={uploadForm.description} 
              onChange={(e) => setUploadForm({...uploadForm, description: e.target.value})} 
              className="retro-textarea" 
              rows="3"
            />
          </div>
          <div className="form-group">
            <label>Tags (comma-separated):</label>
            <input 
              type="text" 
              value={uploadForm.tags} 
              onChange={(e) => setUploadForm({...uploadForm, tags: e.target.value})} 
              className="retro-input" 
              placeholder="nature, landscape, photography"
            />
          </div>
          <div className="form-group">
            <label className="checkbox-label">
              <input 
                type="checkbox" 
                checked={uploadForm.is_featured} 
                onChange={(e) => setUploadForm({...uploadForm, is_featured: e.target.checked})} 
              />
              Featured Image
            </label>
          </div>
          <RetroButton type="submit" disabled={uploading}>
            {uploading ? '📤 Uploading...' : '📤 Upload Image'}
          </RetroButton>
        </form>
      </div>

      {/* Search and Filters */}
      <div className="admin-controls">
        <input 
          type="text" 
          placeholder="Search images..." 
          value={search} 
          onChange={(e) => setSearch(e.target.value)} 
          className="retro-input" 
        />
        <input 
          type="text" 
          placeholder="Filter by tags..." 
          value={selectedTags} 
          onChange={(e) => setSelectedTags(e.target.value)} 
          className="retro-input" 
        />
      </div>

      {/* Tag Cloud */}
      {allTags.length > 0 && (
        <div className="tag-cloud">
          <h4>Available Tags:</h4>
          <div className="tags">
            {allTags.slice(0, 15).map(tag => (
              <span 
                key={tag.name} 
                className={`tag ${selectedTags.includes(tag.name) ? 'active' : ''}`}
                onClick={() => {
                  if (selectedTags.includes(tag.name)) {
                    setSelectedTags(selectedTags.replace(tag.name, '').replace(/,\s*,/g, ',').replace(/^,|,$/g, ''));
                  } else {
                    setSelectedTags(selectedTags ? `${selectedTags}, ${tag.name}` : tag.name);
                  }
                }}
              >
                {tag.name} ({tag.count})
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Edit Form */}
      {editing && (
        <div className="admin-subsection">
          <h4>Edit Image: {editing.title}</h4>
          <form onSubmit={handleUpdate}>
            <div className="form-group">
              <label>Title:</label>
              <input 
                type="text" 
                value={editing.title} 
                onChange={(e) => setEditing({...editing, title: e.target.value})} 
                required 
                className="retro-input" 
              />
            </div>
            <div className="form-group">
              <label>Description:</label>
              <textarea 
                value={editing.description || ''} 
                onChange={(e) => setEditing({...editing, description: e.target.value})} 
                className="retro-textarea" 
                rows="3"
              />
            </div>
            <div className="form-group">
              <label>Tags (comma-separated):</label>
              <input 
                type="text" 
                value={editing.tags ? editing.tags.join(', ') : ''} 
                onChange={(e) => setEditing({...editing, tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)})} 
                className="retro-input" 
              />
            </div>
            <div className="form-group">
              <label className="checkbox-label">
                <input 
                  type="checkbox" 
                  checked={editing.is_featured} 
                  onChange={(e) => setEditing({...editing, is_featured: e.target.checked})} 
                />
                Featured Image
              </label>
            </div>
            <div className="admin-controls">
              <RetroButton type="submit">Update Image</RetroButton>
              <RetroButton type="button" onClick={() => setEditing(null)}>Cancel</RetroButton>
            </div>
          </form>
        </div>
      )}

      {/* Gallery Grid */}
      {galleryData && galleryData.images.length > 0 ? (
        <>
          <div className="admin-gallery-grid">
            {galleryData.images.map(image => (
              <div key={image.id} className="admin-gallery-item">
                <div className="image-container">
                  <img src={image.file_url} alt={image.title} />
                  {image.is_featured && <div className="featured-badge">⭐ Featured</div>}
                </div>
                <div className="image-info">
                  <h5>{image.title}</h5>
                  {image.description && <p className="description">{image.description}</p>}
                  {image.tags && image.tags.length > 0 && (
                    <div className="image-tags">
                      {image.tags.map(tag => (
                        <span key={tag} className="tag">{tag}</span>
                      ))}
                    </div>
                  )}
                  <div className="image-meta">
                    📅 {new Date(image.created_at).toLocaleDateString()}
                    {image.uploaded_by && <span> • 👤 {image.uploaded_by}</span>}
                  </div>
                  <div className="admin-controls">
                    <RetroButton onClick={() => setEditing(image)}>Edit</RetroButton>
                    <RetroButton onClick={() => handleDelete(image.id)}>Delete</RetroButton>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {galleryData.pagination && galleryData.pagination.total_pages > 1 && (
            <div className="pagination">
              <button 
                onClick={() => setPage(Math.max(1, page - 1))} 
                disabled={page === 1}
              >
                Previous
              </button>
              <span className="current-page">
                Page {galleryData.pagination.current_page} of {galleryData.pagination.total_pages}
              </span>
              <button 
                onClick={() => setPage(Math.min(galleryData.pagination.total_pages, page + 1))} 
                disabled={page === galleryData.pagination.total_pages}
              >
                Next
              </button>
            </div>
          )}
        </>
      ) : (
        <div className="empty-state">
          <p>No images in gallery. Upload some images to get started!</p>
        </div>
      )}
    </div>
  );
};

const AdminAnalytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [search, setSearch] = useState('');
  const [country, setCountry] = useState('all');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  useEffect(() => { fetchAnalytics(); }, [search, country, page]);
  const fetchAnalytics = async () => { setLoading(true); try { const params = new URLSearchParams({ page: page.toString(), limit: '20' }); if (search) params.append('search', search); if (country !== 'all') params.append('country', country); const response = await apiCall(`/analytics?${params}`); setAnalytics(response.data); } catch (error) {} finally { setLoading(false); } };
  if (loading && !analytics) return <div>Loading analytics...</div>;
  return (
    <div className="admin-section">
      <h3>📈 Website Analytics</h3>
      {analytics && (<>
        <div className="analytics-overview"><div className="stat-item"><strong>Total Visits:</strong> {analytics.total_visits}</div><div className="stat-item"><strong>Unique Visitors:</strong> {analytics.unique_visitors}</div></div>
        <div className="admin-controls"><input type="text" placeholder="Search IP, browser, URL..." value={search} onChange={(e)=>setSearch(e.target.value)} className="retro-input" /><select value={country} onChange={(e)=>setCountry(e.target.value)} className="retro-input"><option value="all">All Countries</option>{analytics.top_countries.map(c => (<option key={c._id} value={c._id}>{c._id} ({c.count})</option>))}</select></div>
        <h4>Recent Visits</h4>
        <table className="admin-table"><thead><tr><th>Time</th><th>IP Address</th><th>Page</th><th>Browser</th><th>Country</th></tr></thead><tbody>{analytics.recent_visits.map((visit, index) => (<tr key={index}><td>{new Date(visit.timestamp).toLocaleString()}</td><td>{visit.ip_address}</td><td>{visit.page_url}</td><td>{visit.browser}</td><td>{visit.country}</td></tr>))}</tbody></table>
        <div className="pagination"><button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>Previous</button><span className="current-page">Page {analytics.pagination.current_page} of {analytics.pagination.total_pages}</span><button onClick={() => setPage(Math.min(analytics.pagination.total_pages, page + 1))} disabled={page === analytics.pagination.total_pages}>Next</button></div>
        <div className="dashboard-stats"><div className="stat-card"><h4>Top Pages</h4>{analytics.top_pages.map(page => (<div key={page._id}>{page._id}: {page.count} visits</div>))}</div><div className="stat-card"><h4>Top Browsers</h4>{analytics.top_browsers.map(browser => (<div key={browser._id}>{browser._id}: {browser.count} visits</div>))}</div></div>
      </>)}
    </div>
  );
};

const AdminContacts = () => {
  const [contacts, setContacts] = useState(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  useEffect(() => { fetchContacts(); }, [search, page]);
  const fetchContacts = async () => { setLoading(true); try { const params = new URLSearchParams({ page: page.toString(), limit: '10' }); if (search) params.append('search', search); const response = await apiCall(`/contact-messages?${params}`); setContacts(response.data); } catch (error) {} finally { setLoading(false); } };
  const handleDelete = async (messageId) => { if (window.confirm('Delete this message?')) { try { await apiCall(`/contact-messages/${messageId}`, { method: 'DELETE' }); fetchContacts(); } catch (error) { alert('Error deleting message'); } } };
  const mailtoHref = (m) => { const subject = `Re: Your message`; const body = `Hi ${m.name || ''},%0D%0A%0D%0AThanks for reaching out. Below is the message you sent:%0D%0A%0D%0A${encodeURIComponent(m.message)}%0D%0A%0D%0A--%0D%0A`; return `mailto:${encodeURIComponent(m.email)}?subject=${encodeURIComponent(subject)}&body=${body}`; };
  if (loading && !contacts) return <div>Loading contacts...</div>;
  return (
    <div className="admin-section">
      <h3>📧 Contact Messages</h3>
      {contacts && (<>
        <div className="admin-controls"><input type="text" placeholder="Search name, email, message..." value={search} onChange={(e)=>setSearch(e.target.value)} className="retro-input" /></div>
        <table className="admin-table"><thead><tr><th>Date</th><th>Name</th><th>Email</th><th>Message</th><th>IP</th><th>Actions</th></tr></thead><tbody>{contacts.messages.map((message) => (<tr key={message.id}><td>{new Date(message.created_at).toLocaleString()}</td><td>{message.name}</td><td>{message.email}</td><td>{message.message.substring(0, 100)}...</td><td>{message.ip_address}</td><td><a href={mailtoHref(message)} className="nav-button" target="_blank" rel="noopener noreferrer">Reply</a>{' '}<RetroButton onClick={() => handleDelete(message.id)}>Delete</RetroButton></td></tr>))}</tbody></table>
        <div className="pagination"><button onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>Previous</button><span className="current-page">Page {contacts.pagination.current_page} of {contacts.pagination.total_pages}</span><button onClick={() => setPage(Math.min(contacts.pagination.total_pages, page + 1))} disabled={page === contacts.pagination.total_pages}>Next</button></div>
      </>)}
    </div>
  );
};

const AdminSettings = () => {
  const [formData, setFormData] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  useEffect(() => { fetchSettings(); }, []);
  const fetchSettings = async () => { try { const response = await apiCall('/settings'); setFormData(response.data); } catch (error) {} finally { setLoading(false); } };
  const handleUpload = async (e) => { const file = e.target.files?.[0]; if (!file) return; setUploading(true); try { const fd = new FormData(); fd.append('file', file); const res = await apiCall('/upload', { method: 'POST', data: fd, headers: { 'Content-Type': 'multipart/form-data' } }); const fileUrl = `${BACKEND_URL}/api/uploads/${res.data.filename}`; setFormData(prev => ({ ...prev, background_image_url: fileUrl, background_type: 'image' })); alert('Image uploaded. Remember to Save Settings.'); } catch (err) { alert('Upload failed'); } finally { setUploading(false); } };
  const handleSubmit = async (e) => { e.preventDefault(); setSaving(true); try { const formDataObj = new FormData(); const payload = { max_file_size: formData.max_file_size, site_title: formData.site_title || '', site_email: formData.site_email || '', contact_cooldown: formData.contact_cooldown || 300, background_type: formData.background_type || 'default', background_value: formData.background_value || '', background_image_url: formData.background_image_url || '' }; Object.keys(payload).forEach(key => { formDataObj.append(key, payload[key]); }); await apiCall('/settings', { method: 'PUT', data: formDataObj }); alert('Settings updated successfully!'); } catch (error) { alert('Error updating settings'); } finally { setSaving(false); } };
  if (loading) return <div>Loading settings...</div>;
  return (
    <div className="admin-section">
      <h3>⚙️ Website Settings</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group"><label>Site Title:</label><input type="text" value={formData.site_title || ''} onChange={(e)=>setFormData({ ...formData, site_title: e.target.value })} className="retro-input" /></div>
        <div className="form-group"><label>Site Email:</label><input type="email" value={formData.site_email || ''} onChange={(e)=>setFormData({ ...formData, site_email: e.target.value })} className="retro-input" /></div>
        <div className="form-group"><label>Max File Size (bytes):</label><input type="number" value={formData.max_file_size || 5368709120} onChange={(e)=>setFormData({ ...formData, max_file_size: parseInt(e.target.value) })} className="retro-input" /><small>Current: {Math.round((formData.max_file_size || 0) / 1024 / 1024 / 1024)} GB</small></div>
        <div className="form-group"><label>Contact Form Cooldown (seconds):</label><input type="number" value={formData.contact_cooldown || 300} onChange={(e)=>setFormData({ ...formData, contact_cooldown: parseInt(e.target.value) })} className="retro-input" /><small>Current: {Math.round((formData.contact_cooldown || 0) / 60)} minutes</small></div>
        <div className="form-group"><label>Background Type:</label><select value={formData.background_type || 'default'} onChange={(e)=>setFormData({ ...formData, background_type: e.target.value })} className="retro-input"><option value="default">Default (current CSS)</option><option value="color">Solid Color</option><option value="gradient">CSS Gradient</option><option value="image">Image URL</option></select></div>
        {formData.background_type === 'color' && (<div className="form-group"><label>Color (hex or CSS color):</label><input type="text" value={formData.background_value || ''} onChange={(e)=>setFormData({ ...formData, background_value: e.target.value })} className="retro-input" placeholder="#123456 or color name" /></div>)}
        {formData.background_type === 'gradient' && (<div className="form-group"><label>Gradient CSS:</label><input type="text" value={formData.background_value || ''} onChange={(e)=>setFormData({ ...formData, background_value: e.target.value })} className="retro-input" placeholder="e.g., linear-gradient(135deg, #245edc, #1a4298)" /></div>)}
        {formData.background_type === 'image' && (<><div className="form-group"><label>Image URL:</label><input type="text" value={formData.background_image_url || ''} onChange={(e)=>setFormData({ ...formData, background_image_url: e.target.value })} className="retro-input" placeholder="https://..." /></div><div className="form-group"><label>Or upload image:</label><input type="file" accept="image/*" onChange={handleUpload} disabled={uploading} /></div></>)}
        <RetroButton type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save Settings'}</RetroButton>
      </form>
    </div>
  );
};

const PageView = () => {
  const { slug } = useParams();
  const [page, setPage] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const fetchPage = async () => { try { const response = await axios.get(`${API}/page/${slug}`); setPage(response.data); } catch (error) {} finally { setLoading(false); } };
    fetchPage();
  }, [slug]);
  if (loading) return <div className="loading">Loading page...</div>;
  if (!page) return <div className="error">Page not found 😕</div>;
  return (
    <RetroWindow title={page.title} className="main-content">
      <div className="content" dangerouslySetInnerHTML={{ __html: page.content }} />
    </RetroWindow>
  );
};

function App() {
  const [pages] = useState([]);
  useEffect(() => {
    const applyBackground = (s) => {
      if (!s || !s.background_type || s.background_type === 'default') { document.body.style.background = ''; document.body.style.backgroundAttachment = ''; return; }
      if (s.background_type === 'color' || s.background_type === 'gradient') { document.body.style.background = s.background_value || ''; }
      else if (s.background_type === 'image') { document.body.style.background = `url("${s.background_image_url}") center / cover no-repeat fixed`; }
      document.body.style.backgroundAttachment = 'fixed';
    };
    axios.get(`${API}/public-settings`).then(res => { applyBackground(res.data); document.title = res.data.site_title || 'Personal Website Template'; }).catch(() => {});
  }, []);
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Navigation pages={pages} />
          <main className="main-content">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/blog" element={<Blog />} />
              <Route path="/blog/:slug" element={<BlogPost />} />
              <Route path="/gallery" element={<Gallery />} />
              <Route path="/contact" element={<Contact />} />
              <Route path="/login" element={<Login />} />
              <Route path="/first-setup" element={<FirstSetup />} />
              <Route path="/management-panel" element={<Admin />} />
              <Route path="/page/:slug" element={<PageView />} />
            </Routes>
          </main>
          <Footer />
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;