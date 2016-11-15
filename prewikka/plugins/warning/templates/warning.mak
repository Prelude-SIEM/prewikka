<%! from prewikka.utils.html import Markup %>

<script type="text/javascript">
    $(document).ready(function() {
		$('#prewikka-warning').modal();
    });
</script>

<div id="prewikka-warning" class="modal fade" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-backdrop="true" data-keyboard="true" tabindex="-1">
	<div class="modal-dialog modal-lg">
	  <div class="modal-content">
		<div class="modal-header alert-danger">
		  <button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>
		  <h3 class="modal-title title" id="dialogLabel">${ _('WARNING') }</h3>
		</div>
		<div class="modal-body content" style="text-align: center; font-size: 1.1em">
		 	<span style="font-weight: bold; color: red">${ _("Prelude OSS is the open-source version of the Prelude SIEM") }</span>
			<br><br>
			<b><a href="http://www.prelude-siem.com">www.prelude-siem.com</a></b>
			<br><br>
			${ Markup(_("This OSS version has <span style='font-weight: bold'>lower performance</span> and <span style='font-weight: bold'>less <a href='%s'>features</a></span> than the Pro/Enterprise versions.")) % "http://www.prelude-siem.com/index.php/en/products/oss-pro-enterprise" }
			<br>${ _("It is intended for tests and small environments, and should not be used in critical environments.") }

			<br>
			<br>
			${ Markup(_("Prelude OSS is distributed under the %s.")) % Markup("<a href='http://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html'>GNU GPLv2</a>") }
			<br>${ _("Products derivated from Prelude OSS modules are therefore subject to the terms of the GPLv2.") }
		</div>
		<div class="modal-footer">
		  <a class="btn btn-primary ok" aria-hidden="true" data-dismiss="modal">${ _('OK') }</a>
		</div>
	  </div>
	</div>
</div>

