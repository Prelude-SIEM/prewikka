%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

Name:           prewikka
Epoch:          1
Version:        1.0.1
Release:        2%{?dist}
Summary:        Graphical front-end analysis console for the Prelude Hybrid IDS Framework
Group:          Applications/Internet
License:        GPLv2+
URL:            http://www.prelude-ids.org
Source0:        http://www.prelude-ids.org/download/releases/%{name}/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:  python-devel python-cheetah gettext
Requires:       python-cheetah, libprelude-python, libpreludedb-python
BuildArch:      noarch


%description
Prewikka is the graphical front-end analysis console for the
Prelude Universal SIM. Providing numerous features, Prewikka
facilitates the work of users and analysts. It provides alert
aggregation and sensor and hearbeat views, and has user management
and configurable filters.Prewikka also provides access to external
tools such as whois and traceroute.

%prep
%setup -q

%build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --root=%{buildroot}
mkdir -p %{buildroot}%{_defaultdocdir}/%{name}-%{version}
mkdir -p %{buildroot}%{_sbindir}/
chmod 0644 %{buildroot}/%{_datadir}/%{name}/htdocs/css/style.css
mv %{buildroot}/%{_bindir}/%{name}-httpd %{buildroot}/%{_sbindir}/%{name}-httpd
%find_lang %{name}

%clean
rm -rf %{buildroot}

%files -f %{name}.lang
%defattr(-, root, root, -)
%attr(0750, root, apache) %dir %{_sysconfdir}/%{name}/
%config(noreplace) %attr(0640, root, apache) %{_sysconfdir}/%{name}/%{name}.conf
%{_datadir}/%{name}/cgi-bin
%{_datadir}/%{name}/database
%{_datadir}/%{name}/htdocs/css
%attr(0775, root, apache) %{_datadir}/%{name}/htdocs/generated_images
%{_datadir}/%{name}/htdocs/images
%{_datadir}/%{name}/htdocs/js
%{_sbindir}/%{name}-httpd
%{python_sitelib}/%{name}/
%{python_sitelib}/%{name}*.egg-info
%doc AUTHORS README NEWS HACKING.README

%changelog
* Wed Jun 15 2011 Vincent Quéméner <vincent.quemener@c-s.fr> - 1:1.0.0-5
- Fixed the permissions on the generated images directory.

* Wed Jun 15 2011 Vincent Quéméner <vincent.quemener@c-s.fr> - 1:1.0.0-4
- Rebuilt for RHEL6.

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1:1.0.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Jul 21 2010 David Malcolm <dmalcolm@redhat.com> - 1:1.0.0-2
- Rebuilt for https://fedoraproject.org/wiki/Features/Python_2.7/MassRebuild

* Sun May 12 2010 Steve Grubb <sgrubb@redhat.com> 1.0.0-1
- new upstream release

* Wed Feb 12 2010 Steve Grubb <sgrubb@redhat.com> 1.0.0rc3-1
- new upstream release

* Wed Feb 10 2010 Steve Grubb <sgrubb@redhat.com> 1.0.0rc2-1
- new upstream release

* Sat Jan 30 2010 Steve Grubb <sgrubb@redhat.com> 1.0.0rc1-1
- new upstream release

* Tue Sep 29 2009 Steve Grubb <sgrubb@redhat.com> 0.9.17.1-1
- new upstream release

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.17-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Thu Jul 09 2009 Steve Grubb <sgrubb@redhat.com> 0.9.17-1
- new upstream release

* Wed Jun 17 2009 Steve Grubb <sgrubb@redhat.com> 0.9.15-1
- new upstream release

* Fri Apr 17 2009 Steve Grubb <sgrubb@redhat.com> 0.9.14-4
- Change default perms on conf file

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.9.14-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Sat Nov 29 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 0.9.14-2
- Rebuild for Python 2.6

* Thu Apr 24 2008 Steve Grubb <sgrubb@redhat.com> 0.9.14-1
- new upstream release

* Mon Jan 14 2008 Steve Grubb <sgrubb@redhat.com> 0.9.13-1
- new upstream version 0.9.13

* Sun Apr  8 2007 Thorsten Scherf <tscherf@redhat.com> 0.9.10-1
- moved to upstream version 0.9.10

* Sun Jan 12 2007 Thorsten Scherf <tscherf@redhat.com> 0.9.8-1
- moved to upstream version 0.9.8

* Sat Jan 11 2007 Thorsten Scherf <tscherf@redhat.com> 0.9.7.1-5
- changed docs handling
- fixed python settings

* Mon Jan 01 2007 Thorsten Scherf <tscherf@redhat.com> 0.9.7.1-4
- corrected perms on python files
- moved prewikka-httpd to /sbin
- added README.fedora

* Mon Nov 20 2006 Thorsten Scherf <tscherf@redhat.com> 0.9.7.1-3
- disabled dependency-generator

* Mon Nov 20 2006 Thorsten Scherf <tscherf@redhat.com> 0.9.7.1-2
- Some minor fixes in requirements

* Mon Nov 06 2004 Thorsten Scherf <tscherf@redhat.com> 0.9.7.1-1
- test build for fc6



