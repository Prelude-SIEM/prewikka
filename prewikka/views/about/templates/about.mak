<%!
from prewikka import version
%>

<div class="container">
  <div class="widget" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-widget-options="modal-lg">
    <link rel="stylesheet" type="text/css" href="about/css/about.css" />

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">&times;</button>
      <h4 class="modal-title">${ _("Prelude version %s") % version.__version__ }</h4>
    </div>

    <div class="modal-body about">
      <h4>${ _("Prelude is a SIEM (Security Information and Event Management)") }</h4>
      <p>
        ${ _("{prelude} is a security management solution that collects, filters, normalizes, correlates, stores and archives data from various sources of your information system. Based on all this information Prelude can provide a global vision of your system's security level and thus prevent attacks, intrusions as well as viral infections.").format(prelude="<a href='http://www.prelude-siem.com'>Prelude</a>") | n }
      </p>
      <p style="margin-top: 15px"><u>${ _("Prelude Team:")}</u> Gilles Lehmann, Thomas Andrejak, Fran&ccedil;ois Poirotte, Yoann Vandoorselaere, Antoine Luong, Song Tran, Camille Gardet, Abdel Elmili, Cl&eacute;mentine Bourdin, Enguerrand de Mauduit, Avinash Pardessy, Jean-Charles Rogez, S&eacute;lim Menouar, Louis-David Gabet.</p>
      <p style="margin-top: 15px">${ _("Prelude OSS is an open-source project originally created by Yoann Vandoorselaere in 1998.") }</p>

      <h4>${ _("Vigilo is a NMS (Network Management System)") }</h4>
      <p>
        ${ _("{vigilo} is a complete monitoring and performance management solution capable of handling medium and large-scale systems (network - servers - applications) due to its distributed and modular architecture. Vigilo offers all the features required for performance supervision: states and alarms management, metrology, cartography, event correlation and reporting.").format(vigilo="<a href='http://www.vigilo-nms.com'>Vigilo</a>") | n}
      </p>

      <br/>
      <p>
        ${ _("Prelude SIEM and Vigilo NMS are being developed by the %s company, designer, integrator and operator of mission critical systems.") % ("<a href='http://www.c-s.fr'>CS</a>") | n}
      </p>

      <div class="about_contact" class="panel">
        <div>
           <b>${ _("Contact") }</b>
           <p><a href="mailto:contact.prelude@c-s.fr">contact.prelude@c-s.fr</a></p>
           <p><b>${ _("Phone:") }</b> +33 1 41 28 40 00</p>
           <p><b>${ _("Fax:") }</b> +33 1 41 28 40 40</p>
        </div>
        <div>
           <b>${ _("Office") }</b>
           <p>22 avenue Galil&eacute;e</p>
           <p>92350 Le Plessis-Robinson</p>
           <p>France</p>
        </div>
        <div>
           <b>${ _("Websites") }</b>
           <p><a href="http://www.prelude-siem.com">www.prelude-siem.com</a></p>
           <p><a href="http://www.vigilo-nms.com">www.vigilo-nms.com</a></p>
           <p><a href="http://www.c-s.fr">www.c-s.fr</a></p>
        </div>

        <p class="copyright">Copyright &copy; 2004-2017 CS Communication &amp; Syst&egrave;mes. All rights reserved.</p>
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn btn-default widget-only" aria-hidden="true" data-dismiss="modal">${ _('Close') }</button>
    </div>
  </div>
</div>