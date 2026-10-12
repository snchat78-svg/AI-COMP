import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

class EmailVerificationScreen extends StatefulWidget {
  const EmailVerificationScreen({super.key, required this.user});

  final User user;

  @override
  State<EmailVerificationScreen> createState() => _EmailVerificationScreenState();
}

class _EmailVerificationScreenState extends State<EmailVerificationScreen> {
  bool _busy = false;
  bool _verified = false;
  String? _error;
  String? _notice;

  Future<void> _resendVerificationEmail() async {
    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });
    try {
      await widget.user.sendEmailVerification();
      if (mounted) {
        setState(() {
          _notice = 'A new verification link has been sent. Check your inbox and spam folder.';
        });
      }
    } on FirebaseAuthException catch (exception) {
      if (mounted) setState(() => _error = _friendlyError(exception.code));
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'The verification email could not be sent. Check your connection and try again.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _checkVerification() async {
    setState(() {
      _busy = true;
      _error = null;
      _notice = null;
    });
    try {
      await widget.user.reload();
      final refreshedUser = FirebaseAuth.instance.currentUser;
      if (!mounted) return;
      if (refreshedUser?.emailVerified ?? false) {
        setState(() {
          _verified = true;
          _notice = 'Your email is verified. Sign in to continue to AI-COMP.';
        });
      } else {
        setState(() {
          _error = 'Your email is not verified yet. Open the latest link in your email, then check again.';
        });
      }
    } on FirebaseAuthException catch (exception) {
      if (mounted) setState(() => _error = _friendlyError(exception.code));
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Verification status could not be checked. Please try again.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _continueToLogin() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await FirebaseAuth.instance.signOut();
      // The authentication gate displays the login screen after sign-out.
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not return to login. Please try again.');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String _friendlyError(String code) {
    switch (code) {
      case 'too-many-requests':
        return 'Too many attempts. Please wait a little and try again.';
      case 'network-request-failed':
        return 'No network connection. Check your internet and try again.';
      case 'user-disabled':
        return 'This account has been disabled. Contact the administrator.';
      default:
        return 'Firebase could not complete the request ($code). Please try again.';
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Verify email')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 460),
              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Icon(
                        _verified ? Icons.mark_email_read_outlined : Icons.mark_email_unread_outlined,
                        size: 52,
                        color: theme.colorScheme.primary,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        _verified ? 'Email verified' : 'Verify your email address',
                        style: theme.textTheme.headlineSmall,
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        _verified
                            ? 'Your email address has been verified. Sign in again to open your dashboard.'
                            : 'To verify ${widget.user.email ?? 'your email address'}, open the verification link from your inbox. '
                                'If you have not received a link, select "Resend verification email" below. '
                                'You must verify your email before you can sign in to AI-COMP.',
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 16),
                      if (_error != null) ...[
                        Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
                        const SizedBox(height: 8),
                      ],
                      if (_notice != null) ...[
                        Text(
                          _notice!,
                          style: TextStyle(color: theme.colorScheme.primary),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 8),
                      ],
                      if (_verified)
                        FilledButton(
                          onPressed: _busy ? null : _continueToLogin,
                          child: const Text('Continue to login'),
                        )
                      else ...[
                        FilledButton(
                          onPressed: _busy ? null : _checkVerification,
                          child: const Text("I've verified my email"),
                        ),
                        const SizedBox(height: 8),
                        OutlinedButton(
                          onPressed: _busy ? null : _resendVerificationEmail,
                          child: const Text('Resend verification email'),
                        ),
                      ],
                      if (_busy) ...[
                        const SizedBox(height: 12),
                        const Center(child: CircularProgressIndicator()),
                      ],
                      const SizedBox(height: 8),
                      TextButton(
                        onPressed: _busy ? null : () => FirebaseAuth.instance.signOut(),
                        child: const Text('Sign out'),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
