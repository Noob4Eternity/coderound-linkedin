'use client';

import { useState, useEffect } from 'react';
import { Plus, Users, TrendingUp, RefreshCw, Trash2, ExternalLink, Eye, X } from 'lucide-react';
import { supabase, MonitoredProfile, Profile, JobChange } from '../lib/supabase';

interface ProfileDisplay {
  url: string;
  name: string;
  current_position: string | null;
  current_company: string | null;
  last_updated: string | null;
  active: boolean;
}

interface Stats {
  total_profiles: number;
  total_changes: number;
  last_updated: string | null;
}

export default function Dashboard() {
  const [profiles, setProfiles] = useState<ProfileDisplay[]>([]);
  const [stats, setStats] = useState<Stats>({ total_profiles: 0, total_changes: 0, last_updated: null });
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newProfileUrl, setNewProfileUrl] = useState('');
  const [newProfileName, setNewProfileName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<ProfileDisplay | null>(null);
  const [profileDetails, setProfileDetails] = useState<Profile | null>(null);
  const [jobChanges, setJobChanges] = useState<JobChange[]>([]);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [runningCheck, setRunningCheck] = useState(false);
  const [showWarningModal, setShowWarningModal] = useState(false);

  const fetchProfiles = async () => {
    try {
      // Get monitored profiles
      const { data: monitoredProfiles, error: monitoredError } = await supabase
        .from('monitored_profiles')
        .select('url')
        .eq('active', true);

      if (monitoredError) throw monitoredError;

      const result: ProfileDisplay[] = [];

      // For each monitored profile, get the profile data
      for (const monitored of monitoredProfiles || []) {
        const { data: profileData, error: profileError } = await supabase
          .from('profiles')
          .select('*')
          .eq('url', monitored.url)
          .single();

        if (profileData && !profileError) {
          result.push({
            url: monitored.url,
            name: profileData.name || 'Unknown',
            current_position: profileData.current_position,
            current_company: profileData.current_company,
            last_updated: profileData.last_updated,
            active: true
          });
        } else {
          result.push({
            url: monitored.url,
            name: 'Not scraped yet',
            current_position: null,
            current_company: null,
            last_updated: null,
            active: true
          });
        }
      }

      setProfiles(result);
    } catch (error) {
      console.error('Error fetching profiles:', error);
    }
  };

  const fetchStats = async () => {
    try {
      // Get total profiles count
      const { count: profilesCount, error: profilesError } = await supabase
        .from('monitored_profiles')
        .select('*', { count: 'exact', head: true })
        .eq('active', true);

      // Get total changes count
      const { count: changesCount, error: changesError } = await supabase
        .from('job_changes')
        .select('*', { count: 'exact', head: true });

      if (profilesError || changesError) {
        console.error('Error fetching stats:', profilesError || changesError);
        return;
      }

      setStats({
        total_profiles: profilesCount || 0,
        total_changes: changesCount || 0,
        last_updated: null
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const loadData = async () => {
    setLoading(true);
    await Promise.all([fetchProfiles(), fetchStats()]);
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAddProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProfileUrl.trim()) return;

    setSubmitting(true);
    try {
      const { error } = await supabase
        .from('monitored_profiles')
        .insert({
          url: newProfileUrl.trim(),
          name: newProfileName.trim() || null,
          active: true
        });

      if (error) throw error;

      // Immediately scrape the newly added profile
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
        const scrapeResponse = await fetch(`${API_BASE}/api/scrape/${encodeURIComponent(newProfileUrl.trim())}`, {
          method: 'POST',
        });

        if (!scrapeResponse.ok) {
          console.warn('Failed to scrape profile immediately, but it was added to monitoring');
        } else {
          console.log('Profile scraped successfully');
        }
      } catch (scrapeError) {
        console.warn('Failed to scrape profile immediately:', scrapeError);
        // Don't fail the whole operation if scraping fails
      }

      setNewProfileUrl('');
      setNewProfileName('');
      setShowAddForm(false);
      await loadData(); // Refresh data
    } catch (error) {
      console.error('Error adding profile:', error);
      alert('Error adding profile: ' + (error as Error).message);
    }
    setSubmitting(false);
  };

  const handleRemoveProfile = async (url: string) => {
    if (!confirm('Are you sure you want to remove this profile from monitoring?')) return;

    try {
      const { error } = await supabase
        .from('monitored_profiles')
        .delete()
        .eq('url', url);

      if (error) throw error;

      await loadData(); // Refresh data
    } catch (error) {
      console.error('Error removing profile:', error);
      alert('Error removing profile: ' + (error as Error).message);
    }
  };

  const handleViewProfile = async (profile: ProfileDisplay) => {
    setSelectedProfile(profile);
    setShowProfileModal(true);
    setLoadingDetails(true);

    try {
      // Fetch profile details
      const { data: profileData, error: profileError } = await supabase
        .from('profiles')
        .select('*')
        .eq('url', profile.url)
        .single();

      if (profileError) throw profileError;
      setProfileDetails(profileData);

      // Fetch job changes
      const { data: changesData, error: changesError } = await supabase
        .from('job_changes')
        .select('*')
        .eq('profile_url', profile.url)
        .order('detected_at', { ascending: false });

      if (changesError) throw changesError;
      setJobChanges(changesData || []);
    } catch (error) {
      console.error('Error fetching profile details:', error);
      alert('Error loading profile details: ' + (error as Error).message);
    } finally {
      setLoadingDetails(false);
    }
  };

  const closeProfileModal = () => {
    setShowProfileModal(false);
    setSelectedProfile(null);
    setProfileDetails(null);
    setJobChanges([]);
  };

  const handleRunMonitoringCheck = async () => {
    if (runningCheck) return;
    setShowWarningModal(true);
  };

  const confirmRunCheck = async () => {
    setShowWarningModal(false);
    setRunningCheck(true);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
      const response = await fetch(`${API_BASE}/api/run-check`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to run monitoring check');
      }

      const result = await response.json();

      if (result.success) {
        alert('✅ Monitoring check completed successfully! Check for any new job changes.');
        await loadData(); // Refresh the data
      } else {
        throw new Error(result.message || 'Unknown error occurred');
      }
    } catch (error) {
      console.error('Error running monitoring check:', error);
      alert('❌ Error running monitoring check: ' + (error as Error).message);
    } finally {
      setRunningCheck(false);
    }
  };

  const cancelRunCheck = () => {
    setShowWarningModal(false);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const extractProfileId = (url: string) => {
    const match = url.match(/linkedin\.com\/in\/([^\/]+)/);
    return match ? match[1] : url;
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="text-slate-900">
              <h1 className="text-3xl font-bold">LinkedIn Job Monitor</h1>
              <p className="text-slate-600 mt-1">Monitor LinkedIn profiles for job changes</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleRunMonitoringCheck}
                disabled={runningCheck}
                className="inline-flex items-center px-4 py-2 border border-slate-300 rounded-lg shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors duration-200"
              >
                <TrendingUp className={`h-4 w-4 mr-2 ${runningCheck ? 'animate-pulse' : ''}`} />
                {runningCheck ? 'Running...' : 'Check All'}
              </button>
              <button
                onClick={loadData}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-slate-300 rounded-lg shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors duration-200"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-slate-900 mb-2">
            Welcome to your LinkedIn Job Monitor
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Stay ahead of career moves with automated monitoring and instant notifications when your network makes job changes.
          </p>
        </div>
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-slate-600">Monitored Profiles</h3>
                <p className="text-3xl font-bold text-slate-900 mt-1">{stats.total_profiles}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 bg-green-50 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-green-600" />
                </div>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-slate-600">Job Changes Detected</h3>
                <p className="text-3xl font-bold text-slate-900 mt-1">{stats.total_changes}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow duration-200">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <RefreshCw className="h-6 w-6 text-slate-600" />
                </div>
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-slate-600">Last Updated</h3>
                <p className="text-lg font-semibold text-slate-900 mt-1">{formatDate(stats.last_updated)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Add Profile Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
          >
            <Plus className="h-5 w-5 mr-2" />
            Add Profile to Monitor
          </button>
        </div>

        {/* Add Profile Form */}
        {showAddForm && (
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
              <Plus className="h-5 w-5 mr-2 text-blue-600" />
              Add New Profile
            </h2>
            <form onSubmit={handleAddProfile} className="space-y-4">
              <div>
                <label htmlFor="url" className="block text-sm font-medium text-slate-700 mb-1">
                  LinkedIn Profile URL *
                </label>
                <input
                  type="url"
                  id="url"
                  required
                  value={newProfileUrl}
                  onChange={(e) => setNewProfileUrl(e.target.value)}
                  placeholder="https://www.linkedin.com/in/username"
                  className="block w-full border-slate-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2"
                />
              </div>
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-1">
                  Display Name (Optional)
                </label>
                <input
                  type="text"
                  id="name"
                  value={newProfileName}
                  onChange={(e) => setNewProfileName(e.target.value)}
                  placeholder="John Doe"
                  className="block w-full border-slate-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors duration-200"
                >
                  {submitting ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin inline" />
                      Adding...
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4 mr-2 inline" />
                      Add Profile
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Profiles List */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center">
              <Users className="h-5 w-5 mr-2 text-blue-600" />
              Monitored Profiles
            </h2>
            <p className="text-slate-600 mt-1">Profiles currently being monitored for job changes</p>
          </div>

          {loading ? (
            <div className="p-8 text-center">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-blue-500 mb-2" />
              <p className="text-slate-600">Loading profiles...</p>
            </div>
          ) : profiles.length === 0 ? (
            <div className="p-8 text-center">
              <div className="p-3 bg-blue-50 rounded-full w-12 h-12 mx-auto mb-4 flex items-center justify-center">
                <Users className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="text-sm font-medium text-slate-900 mb-1">No profiles monitored</h3>
              <p className="text-slate-600 text-sm">Get started by adding a LinkedIn profile to monitor.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Profile
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Current Position
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Last Updated
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {profiles.map((profile, index) => (
                    <tr key={index} className="hover:bg-slate-50 transition-colors duration-200">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-semibold text-sm">
                              {profile.name.charAt(0).toUpperCase()}
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-slate-900">
                              {profile.name}
                            </div>
                            <div className="text-sm text-slate-500">
                              {extractProfileId(profile.url)}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-slate-900">
                          {profile.current_position || 'Not available'}
                        </div>
                        <div className="text-sm text-slate-500">
                          {profile.current_company || ''}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                        {formatDate(profile.last_updated)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end space-x-2">
                          <button
                            onClick={() => handleViewProfile(profile)}
                            className="p-1.5 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors duration-200"
                            title="View Details"
                          >
                            <Eye className="h-4 w-4" />
                          </button>
                          <a
                            href={profile.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 text-green-600 hover:text-green-800 hover:bg-green-50 rounded transition-colors duration-200"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                          <button
                            onClick={() => handleRemoveProfile(profile.url)}
                            className="p-1.5 text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors duration-200"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Profile Details Modal */}
      {showProfileModal && selectedProfile && (
        <div className="fixed inset-0 bg-black/50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
          <div className="relative w-full max-w-4xl bg-white rounded-2xl shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-50 border-b border-slate-200 rounded-t-2xl p-6">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-4">
                  <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-lg">
                    {selectedProfile.name.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-slate-900">
                      Profile Details
                    </h3>
                    <p className="text-slate-600">{selectedProfile.name}</p>
                  </div>
                </div>
                <button
                  onClick={closeProfileModal}
                  className="p-2 hover:bg-slate-100 rounded-lg transition-colors duration-200"
                >
                  <X className="h-5 w-5 text-slate-500" />
                </button>
              </div>
            </div>

            <div className="p-6">
              {loadingDetails ? (
                <div className="flex justify-center items-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mr-3" />
                  <span className="text-slate-600">Loading profile details...</span>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Profile Information */}
                  <div className="bg-slate-50 rounded-lg p-6">
                    <h4 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                      <Users className="h-5 w-5 mr-2 text-blue-600" />
                      Profile Information
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Name</label>
                        <p className="text-slate-900 font-medium">{profileDetails?.name || 'Not available'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Current Position</label>
                        <p className="text-slate-900 font-medium">{profileDetails?.current_position || 'Not available'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Current Company</label>
                        <p className="text-slate-900 font-medium">{profileDetails?.current_company || 'Not available'}</p>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1">Last Updated</label>
                        <p className="text-slate-900 font-medium">{formatDate(profileDetails?.last_updated || null)}</p>
                      </div>
                    </div>
                    <div className="mt-4">
                      <label className="block text-sm font-medium text-slate-700 mb-1">LinkedIn URL</label>
                      <a
                        href={selectedProfile.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 hover:underline transition-colors duration-200"
                      >
                        {selectedProfile.url}
                      </a>
                    </div>
                  </div>

                  {/* Job Changes History */}
                  <div>
                    <h4 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
                      <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
                      Job Changes History
                    </h4>
                    {jobChanges.length === 0 ? (
                      <div className="text-center py-12 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="p-4 bg-green-50 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                          <TrendingUp className="h-8 w-8 text-green-600" />
                        </div>
                        <h5 className="text-lg font-medium text-slate-900 mb-1">No job changes detected yet</h5>
                        <p className="text-slate-600">Job changes will appear here when detected</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {jobChanges.map((change, index) => (
                          <div key={index} className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow duration-200">
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-3">
                                  <div className="p-1.5 bg-green-100 rounded">
                                    <TrendingUp className="h-4 w-4 text-green-600" />
                                  </div>
                                  <span className="font-medium text-slate-900">Job Change Detected</span>
                                </div>
                                <div className="space-y-2">
                                  <div className="bg-red-50 rounded p-3 border border-red-200">
                                    <p className="text-xs font-medium text-red-700 mb-1">Previous Position</p>
                                    <p className="text-slate-900 text-sm">
                                      {change.old_position || 'Unknown'} {change.old_company && `at ${change.old_company}`}
                                    </p>
                                  </div>
                                  <div className="bg-green-50 rounded p-3 border border-green-200">
                                    <p className="text-xs font-medium text-green-700 mb-1">New Position</p>
                                    <p className="text-slate-900 text-sm">
                                      {change.new_position || 'Unknown'} {change.new_company && `at ${change.new_company}`}
                                    </p>
                                  </div>
                                </div>
                              </div>
                              <div className="text-right ml-4">
                                <p className="text-xs text-slate-500 mb-2">
                                  Detected: {formatDate(change.detected_at)}
                                </p>
                                {change.notified && (
                                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                    ✓ Notified
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="flex justify-end mt-6 pt-4 border-t border-slate-200">
                <button
                  onClick={closeProfileModal}
                  className="px-6 py-2 bg-slate-600 text-white font-medium rounded-lg shadow-sm hover:bg-slate-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-500 transition-colors duration-200"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Warning Modal */}
      {showWarningModal && (
        <div className="fixed inset-0 bg-black/50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
          <div className="relative w-full max-w-md bg-white rounded-2xl shadow-xl">
            <div className="p-6">
              <div className="flex items-center mb-4">
                <div className="flex-shrink-0">
                  <div className="p-3 bg-amber-100 rounded-full">
                    <svg className="h-6 w-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                    </svg>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-slate-900">Web Scraping Warning</h3>
                </div>
              </div>

              <div className="mb-6">
                <p className="text-slate-600 mb-4">
                  You are about to run a web scraper that will:
                </p>
                <ul className="space-y-2 text-sm text-slate-600">
                  <li className="flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    Visit LinkedIn profiles for all monitored users
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    Extract job change information
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-500 mr-2">•</span>
                    May take several minutes to complete
                  </li>
                  <li className="flex items-start">
                    <span className="text-amber-600 mr-2">⚠️</span>
                    Could be detected by LinkedIn
                  </li>
                </ul>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={cancelRunCheck}
                  className="px-4 py-2 border border-slate-300 rounded-lg shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmRunCheck}
                  className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors duration-200"
                >
                  Continue
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
