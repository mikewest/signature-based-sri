# Signature-based Integrity

## [Security and Privacy Questionnaire](https://www.w3.org/TR/security-privacy-questionnaire/) Answers

### What information might this feature expose to Web sites or other parties, and for what purposes is that exposure necessary?

The user agent will not expose any additional information through this feature.

Servers relying upon this feature for their resources will expose a public signing key to sites that embed those resources, by delivering that key along with the response in a `Signature-Input` header, and exposing that response to the site through CORS headers. This is necessary to ensure both that the resource itself is signed in a way that proves its provenance, and to allow sites that depend on the resource to make assertions about the resources' provenance that browsers can enforce.

Sites relying upon this feature will expose their reliance to other parties, advertising the public signing key they expect for a given resource by embedding an `Accept-Signature` header into outgoing requests that enforce signature-based integrity. This is necessary to support key rotation.

### Do features in your specification expose the minimum amount of information necessary to enable their intended uses?

I believe so. We could likely get away without the `Accept-Signature` header (at the cost of deployment complexity), but I don't think we can easily prevent public keys from becoming available.

### How do the features in your specification deal with personal information, personally-identifiable information (PII), or information derived from them?

They do not.

### How do the features in your specification deal with sensitive information?

They do not.

### Do the features in your specification introduce new state for an origin that persists across browsing sessions?

It does not. The mechanism will rely upon HTTP caching, just as Fetch does generally.

### Do the features in your specification expose information about the underlying platform to origins?

It does not.

### Does this specification allow an origin to send data to the underlying platform?

It does not.

### Do features in this specification enable access to device sensors?

They do not.

### Do features in this specification enable new script execution/loading mechanisms?

No. This specification defines the opposite, allowing sites to place new restrictions upon the script executing on their pages.

### Do features in this specification allow an origin to access other devices?

They do not.

### Do features in this specification allow an origin some measure of control over a user agent’s native UI?

It does not.

### What temporary identifiers do the features in this specification create or expose to the web?

Sites can broadcast an identifier by abusing the `Accept-Signature` header. This, however, is no different from broadcasting the same identifier via a GET parameter in the request itself. I don't believe new communication channels are produced.

### How does this specification distinguish between behavior in first-party and third-party contexts?

It does not. Signatures can be enforced for any resource, regardless of origin.

### How do the features in this specification work in the context of a browser’s Private Browsing or Incognito mode?

This feature is likely unaffected by private modes, except insofar as those modes effect the persistence of caches.

### Does this specification have both "Security Considerations" and "Privacy Considerations" sections?

It does: [Privacy](https://wicg.github.io/signature-based-sri/#privacy), [Security](https://wicg.github.io/signature-based-sri/#security).

### Do features in your specification enable origins to downgrade default security protections?

No. This specification defines new security protections folks can opt-into, but it provides no ability to opt-out of default protections.

### How does your feature handle non-"fully active" documents?

No special considerations are necessary. If resource fetches happen in this state, the same enforcements will remain in place, as they're modeled to happen at the network layer.

### What should this questionnaire have asked?

For this particular feature, I don't think there are additional relevant questions.
