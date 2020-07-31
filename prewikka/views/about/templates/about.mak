<%!
from prewikka import version
%>

<div class="container">
  <div class="widget" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-widget-options="modal-lg">
    <link rel="stylesheet" type="text/css" href="about/css/about.css" />

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">&times;</button>
      <h5 class="modal-title">${ _("Prelude SIEM version %s") % version.__version__ }</h5>
    </div>

    <div class="modal-body about">
      <h5>${ _("Prelude SIEM is a \"Security Information and Event Management\" system") }</h5>
      <div class="software">
        <div class="col-sm-3">
          <img src="about/images/prelude-logo-400.png"/>
        </div>
        <p class="col-sm-9">
          ${ _("{prelude} is a security management solution that collects, filters, normalizes, correlates, stores and archives data from various sources of your information system. Based on all this information Prelude SIEM can provide a global vision of your system's security level and thus prevent attacks, intrusions as well as viral infections.").format(prelude="<a href='https://www.prelude-siem.com'>Prelude SIEM</a>") | n }
        </p>
      </div>

      <br/>
      <h5>${ _("Vigilo NMS is a \"Network Monitoring System\"") }</h5>
      <div class="software">
        <div class="col-sm-3">
          <img src="about/images/vigilo-logo-400.png"/>
        </div>
        <p class="col-sm-9">
          ${ _("{vigilo} is a complete monitoring and performance management solution capable of handling medium and large-scale systems (network - servers - applications) due to its distributed and modular architecture. Vigilo NMS offers all the features required for performance supervision: states and alarms management, metrology, cartography, event correlation and reporting.").format(vigilo="<a href='https://www.vigilo-nms.com'>Vigilo NMS</a>") | n}
        </p>
      </div>

      <br/>
      <p>
        ${ _("Prelude SIEM and Vigilo NMS are being developed by the %s company, designer, integrator and operator of mission critical systems.") % ("<a href='http://www.csgroup.eu'>CS GROUP</a>") | n}
      </p>

      <div class="about_contact" class="panel">
        <div>
           <b>${ _("Contact") }</b>
           <p><a href="mailto:contact.prelude@csgroup.eu">contact.prelude@csgroup.eu</a></p>
           <p><b>${ _("Phone:") }</b> +33 1 41 28 40 00</p>
           <p><b>${ _("Fax:") }</b> +33 1 41 28 40 40</p>
        </div>
        <div>
           <b>${ _("Corporate") }</b>
           <p><a href="https://www.prelude-siem.com">www.prelude-siem.com</a></p>
           <p><a href="https://www.vigilo-nms.com">www.vigilo-nms.com</a></p>
           <p><a href="http://www.csgroup.eu">www.csgroup.eu</a></p>
        </div>
        <div>
           <b>${ _("Community") }</b>
           <p><a href="https://www.prelude-siem.org">www.prelude-siem.org</a></p>
           <p><a href="https://www.vigilo-nms.org">www.vigilo-nms.org</a></p>
        </div>

        <p class="copyright">Copyright &copy; 2004-2020 CS GROUP - France. All rights reserved.</p>
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn btn-default widget-only" aria-hidden="true" data-dismiss="modal">${ _('Close') }</button>
    </div>
  </div>
</div>
