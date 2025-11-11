'use client';

import { useState, useEffect } from 'react';
import { Plus, Users, TrendingUp, RefreshCw, Trash2, ExternalLink } from 'lucide-react';
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

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const extractProfileId = (url: string) => {
    const match = url.match(/linkedin\.com\/in\/([^\/]+)/);
    return match ? match[1] : url;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">LinkedIn Job Monitor</h1>
              <p className="text-gray-600 mt-1">Monitor LinkedIn profiles for job changes</p>
            </div>
            <button
              onClick={loadData}
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Monitored Profiles</h3>
                <p className="text-2xl font-bold text-gray-700">{stats.total_profiles}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Job Changes Detected</h3>
                <p className="text-2xl font-bold text-gray-700">{stats.total_changes}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <RefreshCw className="h-8 w-8 text-gray-600" />
              </div>
              <div className="ml-4">
                <h3 className="text-lg font-medium text-gray-900">Last Updated</h3>
                <p className="text-sm text-gray-600">{formatDate(stats.last_updated)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Add Profile Button */}
        <div className="mb-6">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Profile to Monitor
          </button>
        </div>

        {/* Add Profile Form */}
        {showAddForm && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Add New Profile</h2>
            <form onSubmit={handleAddProfile} className="space-y-4">
              <div>
                <label htmlFor="url" className="block text-sm font-medium text-gray-700">
                  LinkedIn Profile URL *
                </label>
                <input
                  type="url"
                  id="url"
                  required
                  value={newProfileUrl}
                  onChange={(e) => setNewProfileUrl(e.target.value)}
                  placeholder="https://www.linkedin.com/in/username"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Display Name (Optional)
                </label>
                <input
                  type="text"
                  id="name"
                  value={newProfileName}
                  onChange={(e) => setNewProfileName(e.target.value)}
                  placeholder="John Doe"
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  {submitting ? 'Adding...' : 'Add Profile'}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Profiles List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Monitored Profiles</h2>
            <p className="text-sm text-gray-600 mt-1">Profiles currently being monitored for job changes</p>
          </div>

          {loading ? (
            <div className="p-6 text-center">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto text-gray-400" />
              <p className="mt-2 text-gray-600">Loading profiles...</p>
            </div>
          ) : profiles.length === 0 ? (
            <div className="p-6 text-center">
              <Users className="h-12 w-12 mx-auto text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No profiles monitored</h3>
              <p className="mt-1 text-sm text-gray-600">Get started by adding a LinkedIn profile to monitor.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Profile
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Current Position
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Updated
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {profiles.map((profile, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {profile.name}
                            </div>
                            <div className="text-sm text-gray-500">
                              {extractProfileId(profile.url)}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">
                          {profile.current_position || 'Not available'}
                        </div>
                        <div className="text-sm text-gray-500">
                          {profile.current_company || ''}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(profile.last_updated)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end space-x-2">
                          <a
                            href={profile.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-900"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                          <button
                            onClick={() => handleRemoveProfile(profile.url)}
                            className="text-red-600 hover:text-red-900"
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
    </div>
  );
}
